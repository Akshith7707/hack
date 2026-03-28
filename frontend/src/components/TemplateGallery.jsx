import { useState, useEffect } from 'react';
import { getTemplates, getTemplateCategories, cloneTemplate } from '../api';
import './TemplateGallery.css';

function TemplateGallery({ onClone, onClose }) {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cloning, setCloning] = useState(null);

  useEffect(() => {
    loadData();
  }, [selectedCategory]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [templatesData, categoriesData] = await Promise.all([
        getTemplates(selectedCategory),
        getTemplateCategories()
      ]);
      setTemplates(templatesData);
      setCategories(categoriesData);
    } catch (err) {
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClone = async (templateId) => {
    setCloning(templateId);
    try {
      const workflow = await cloneTemplate(templateId);
      onClone(workflow);
    } catch (err) {
      console.error('Failed to clone template:', err);
    } finally {
      setCloning(null);
    }
  };

  const featuredTemplates = templates.filter(t => t.is_featured);
  const regularTemplates = templates.filter(t => !t.is_featured);

  return (
    <div className="template-gallery-overlay">
      <div className="template-gallery">
        <div className="gallery-header">
          <h2>Workflow Templates</h2>
          <button className="btn-close" onClick={onClose}>x</button>
        </div>

        <div className="gallery-categories">
          <button
            className={`category-pill ${!selectedCategory ? 'active' : ''}`}
            onClick={() => setSelectedCategory(null)}
          >
            All Templates
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              className={`category-pill ${selectedCategory === cat.id ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat.id)}
            >
              <span className="cat-icon">{cat.icon}</span> {cat.name}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="gallery-loading">Loading templates...</div>
        ) : (
          <div className="gallery-content">
            {featuredTemplates.length > 0 && (
              <section className="template-section">
                <h3>Featured</h3>
                <div className="template-grid">
                  {featuredTemplates.map(template => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      onClone={handleClone}
                      cloning={cloning === template.id}
                    />
                  ))}
                </div>
              </section>
            )}

            {regularTemplates.length > 0 && (
              <section className="template-section">
                <h3>All Templates</h3>
                <div className="template-grid">
                  {regularTemplates.map(template => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      onClone={handleClone}
                      cloning={cloning === template.id}
                    />
                  ))}
                </div>
              </section>
            )}

            {templates.length === 0 && (
              <div className="gallery-empty">
                <p>No templates found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TemplateCard({ template, onClone, cloning }) {
  return (
    <div className="template-card">
      <div className="template-icon">{template.icon}</div>
      <div className="template-info">
        <h4>{template.name}</h4>
        <p>{template.description}</p>
        <div className="template-meta">
          <span className="template-category">{template.category}</span>
          <span className="template-usage">{template.use_count || 0} uses</span>
        </div>
      </div>
      <button
        className="btn-use-template"
        onClick={() => onClone(template.id)}
        disabled={cloning}
      >
        {cloning ? 'Creating...' : 'Use Template'}
      </button>
    </div>
  );
}

export default TemplateGallery;
