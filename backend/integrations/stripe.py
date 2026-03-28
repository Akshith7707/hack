"""
Stripe Integration
Handles payment-related triggers and actions
"""
import os
import httpx
from typing import Dict, List
from .base import Integration


class StripeIntegration(Integration):
    """
    Stripe integration for payment workflows.
    Requires STRIPE_API_KEY (secret key) environment variable.
    """

    name = "stripe"
    description = "Payment processing and customer management"
    icon = "S"

    API_BASE = "https://api.stripe.com/v1"

    DEFAULT_API_KEY = os.environ.get("STRIPE_API_KEY")

    def _get_auth(self, api_key: str = None) -> tuple:
        key = api_key or self.DEFAULT_API_KEY
        return (key, "")

    @property
    def triggers(self) -> List[Dict]:
        return [
            {
                "id": "payment_failed",
                "name": "Payment Failed",
                "description": "Triggered when a payment fails"
            },
            {
                "id": "subscription_canceled",
                "name": "Subscription Canceled",
                "description": "Triggered when subscription is canceled"
            },
            {
                "id": "invoice_upcoming",
                "name": "Invoice Upcoming",
                "description": "Triggered before invoice is due"
            }
        ]

    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "create_customer",
                "name": "Create Customer",
                "description": "Create a new Stripe customer"
            },
            {
                "id": "get_customer",
                "name": "Get Customer Info",
                "description": "Retrieve customer details"
            },
            {
                "id": "send_invoice",
                "name": "Send Invoice",
                "description": "Create and send an invoice"
            },
            {
                "id": "create_payment_link",
                "name": "Create Payment Link",
                "description": "Generate a payment link"
            }
        ]

    @property
    def config_schema(self) -> Dict:
        return {
            "api_key": {
                "type": "string",
                "description": "Stripe Secret Key (sk_...)",
                "required": False
            },
            "webhook_secret": {
                "type": "string",
                "description": "Stripe webhook signing secret",
                "required": False
            }
        }

    async def trigger(self, config: Dict) -> List[Dict]:
        """
        Stripe triggers are webhook-based.
        This method polls recent events for testing.
        """
        api_key = config.get("api_key") or self.DEFAULT_API_KEY
        if not api_key:
            return [{"error": "No Stripe API key configured"}]

        auth = self._get_auth(api_key)
        event_type = config.get("event_type", "payment_intent.payment_failed")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/events",
                    auth=auth,
                    params={"type": event_type, "limit": 10}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    return [{"error": f"Stripe API error: {response.status_code}"}]
        except httpx.TimeoutException:
            return [{"error": "Stripe request timed out"}]
        except Exception as e:
            return [{"error": str(e)}]

    async def action(self, config: Dict, data: Dict) -> Dict:
        """Execute a Stripe action"""
        action_type = config.get("action_type", "get_customer")
        api_key = config.get("api_key") or self.DEFAULT_API_KEY

        if not api_key:
            return {
                "status": "skipped",
                "reason": "No Stripe API key configured. Set STRIPE_API_KEY env var."
            }

        auth = self._get_auth(api_key)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if action_type == "create_customer":
                    return await self._create_customer(client, auth, data)
                elif action_type == "get_customer":
                    return await self._get_customer(client, auth, data)
                elif action_type == "send_invoice":
                    return await self._send_invoice(client, auth, data)
                elif action_type == "create_payment_link":
                    return await self._create_payment_link(client, auth, config, data)
                else:
                    return {"status": "error", "error": f"Unknown action: {action_type}"}
        except httpx.TimeoutException:
            return {"status": "error", "error": "Stripe request timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _create_customer(self, client, auth, data: Dict) -> Dict:
        """Create a new Stripe customer"""
        payload = {}

        if data.get("email"):
            payload["email"] = data["email"]
        if data.get("name"):
            payload["name"] = data["name"]
        if data.get("phone"):
            payload["phone"] = data["phone"]
        if data.get("description"):
            payload["description"] = data["description"]

        if data.get("metadata"):
            for key, value in data["metadata"].items():
                payload[f"metadata[{key}]"] = str(value)

        response = await client.post(
            f"{self.API_BASE}/customers",
            auth=auth,
            data=payload
        )

        if response.status_code == 200:
            customer = response.json()
            return {
                "status": "success",
                "customer_id": customer["id"],
                "email": customer.get("email")
            }
        else:
            return {"status": "error", "error": response.text[:500]}

    async def _get_customer(self, client, auth, data: Dict) -> Dict:
        """Get customer information"""
        customer_id = data.get("customer_id")
        email = data.get("email")

        if customer_id:
            response = await client.get(
                f"{self.API_BASE}/customers/{customer_id}",
                auth=auth
            )
        elif email:
            response = await client.get(
                f"{self.API_BASE}/customers",
                auth=auth,
                params={"email": email, "limit": 1}
            )
            if response.status_code == 200:
                customers = response.json().get("data", [])
                if customers:
                    return {"status": "success", "customer": customers[0]}
                else:
                    return {"status": "not_found", "message": f"No customer with email {email}"}
            else:
                return {"status": "error", "error": response.text[:500]}
        else:
            return {"status": "error", "error": "customer_id or email required"}

        if response.status_code == 200:
            return {"status": "success", "customer": response.json()}
        else:
            return {"status": "error", "error": response.text[:500]}

    async def _send_invoice(self, client, auth, data: Dict) -> Dict:
        """Create and send an invoice"""
        customer_id = data.get("customer_id")

        if not customer_id:
            return {"status": "error", "error": "customer_id required"}

        invoice_data = {
            "customer": customer_id,
            "auto_advance": "true",
        }

        if data.get("description"):
            invoice_data["description"] = data["description"]

        if data.get("collection_method"):
            invoice_data["collection_method"] = data["collection_method"]

        response = await client.post(
            f"{self.API_BASE}/invoices",
            auth=auth,
            data=invoice_data
        )

        if response.status_code != 200:
            return {"status": "error", "error": f"Failed to create invoice: {response.text[:500]}"}

        invoice = response.json()
        invoice_id = invoice["id"]

        for item in data.get("items", []):
            amount = int(float(item.get("amount", 0)) * 100)
            await client.post(
                f"{self.API_BASE}/invoiceitems",
                auth=auth,
                data={
                    "customer": customer_id,
                    "invoice": invoice_id,
                    "amount": str(amount),
                    "currency": item.get("currency", "usd"),
                    "description": item.get("description", "Item")
                }
            )

        finalize_response = await client.post(
            f"{self.API_BASE}/invoices/{invoice_id}/finalize",
            auth=auth
        )

        if finalize_response.status_code == 200:
            final_invoice = finalize_response.json()
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "invoice_url": final_invoice.get("hosted_invoice_url"),
                "amount_due": final_invoice.get("amount_due")
            }
        else:
            return {
                "status": "partial",
                "invoice_id": invoice_id,
                "message": "Invoice created but not finalized"
            }

    async def _create_payment_link(self, client, auth, config, data: Dict) -> Dict:
        """Create a payment link"""
        price_id = data.get("price_id")
        amount = data.get("amount")
        product_name = data.get("product_name", "Payment")

        if not price_id and not amount:
            return {"status": "error", "error": "price_id or amount required"}

        if price_id:
            payload = {
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": str(data.get("quantity", 1))
            }
        else:
            amount_cents = int(float(amount) * 100)
            product_response = await client.post(
                f"{self.API_BASE}/products",
                auth=auth,
                data={"name": product_name}
            )

            if product_response.status_code != 200:
                return {"status": "error", "error": "Failed to create product"}

            product_id = product_response.json()["id"]

            price_response = await client.post(
                f"{self.API_BASE}/prices",
                auth=auth,
                data={
                    "product": product_id,
                    "unit_amount": str(amount_cents),
                    "currency": data.get("currency", "usd")
                }
            )

            if price_response.status_code != 200:
                return {"status": "error", "error": "Failed to create price"}

            price_id = price_response.json()["id"]

            payload = {
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": str(data.get("quantity", 1))
            }

        response = await client.post(
            f"{self.API_BASE}/payment_links",
            auth=auth,
            data=payload
        )

        if response.status_code == 200:
            link = response.json()
            return {
                "status": "success",
                "payment_link_id": link["id"],
                "url": link["url"]
            }
        else:
            return {"status": "error", "error": response.text[:500]}
