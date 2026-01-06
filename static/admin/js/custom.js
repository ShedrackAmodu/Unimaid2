// Custom Admin JavaScript for Ramat Library

document.addEventListener('DOMContentLoaded', function() {
    // Add loading animation to submit buttons
    const submitButtons = document.querySelectorAll('input[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.value;
            this.value = 'Processing...';
            this.disabled = true;
            this.style.opacity = '0.7';

            // Restore after 5 seconds (in case of error)
            setTimeout(() => {
                this.value = originalText;
                this.disabled = false;
                this.style.opacity = '1';
            }, 5000);
        });
    });

    // Enhance filter functionality
    const filterInputs = document.querySelectorAll('#changelist-filter input[type="text"]');
    filterInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const items = this.closest('ul').querySelectorAll('li');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(value)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    // Add confirmation to delete links
    const deleteLinks = document.querySelectorAll('.deletelink');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Enhance select all functionality
    const actionSelect = document.getElementById('action-toggle');
    if (actionSelect) {
        actionSelect.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input.action-select');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // Add search highlighting
    const searchParams = new URLSearchParams(window.location.search);
    const searchQuery = searchParams.get('q');
    if (searchQuery) {
        const results = document.querySelectorAll('#result_list td');
        results.forEach(td => {
            const html = td.innerHTML;
            const highlighted = html.replace(
                new RegExp(searchQuery, 'gi'),
                match => `<span class="search-highlight">${match}</span>`
            );
            td.innerHTML = highlighted;
        });
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('searchbar');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to clear search
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('searchbar');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.form.submit();
            }
        }
    });

    // Add tooltips
    const tooltipElements = document.querySelectorAll('[title]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = this.getAttribute('title');
            tooltip.style.position = 'absolute';
            tooltip.style.background = '#0a2472';
            tooltip.style.color = 'white';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '0.9rem';
            tooltip.style.zIndex = '10000';
            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            tooltip.style.left = (rect.left + (rect.width - tooltip.offsetWidth) / 2) + 'px';

            this._tooltip = tooltip;
        });

        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });

    // Add animation to table rows
    const tableRows = document.querySelectorAll('#result_list tbody tr');
    tableRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(20px)';

        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 50);
    });

    // Add status indicator to action column
    const actionColumns = document.querySelectorAll('td.field-_actions');
    actionColumns.forEach(td => {
        const row = td.closest('tr');
        const statusElement = row.querySelector('.field-status');
        if (statusElement) {
            const status = statusElement.textContent.trim().toLowerCase();
            td.style.borderLeft = `4px solid ${getStatusColor(status)}`;
        }
    });

    function getStatusColor(status) {
        const colors = {
            'active': '#28a745',
            'inactive': '#dc3545',
            'pending': '#ffc107',
            'published': '#007bff',
            'draft': '#6c757d',
            'available': '#28a745',
            'checked_out': '#ffc107',
            'lost': '#dc3545',
            'damaged': '#6c757d',
            'returned': '#17a2b8',
            'overdue': '#dc3545',
        };
        return colors[status] || '#6c757d';
    }

    // Add live date/time in header
    function updateDateTime() {
        const now = new Date();
        const dateTimeStr = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();

        let dateTimeElement = document.getElementById('admin-datetime');
        if (!dateTimeElement) {
            dateTimeElement = document.createElement('div');
            dateTimeElement.id = 'admin-datetime';
            dateTimeElement.style.position = 'fixed';
            dateTimeElement.style.top = '10px';
            dateTimeElement.style.right = '10px';
            dateTimeElement.style.background = 'rgba(10, 36, 114, 0.9)';
            dateTimeElement.style.color = 'white';
            dateTimeElement.style.padding = '5px 10px';
            dateTimeElement.style.borderRadius = '4px';
            dateTimeElement.style.fontSize = '0.9rem';
            dateTimeElement.style.zIndex = '1000';
            document.body.appendChild(dateTimeElement);
        }

        dateTimeElement.textContent = dateTimeStr;
    }

    // Update date/time every second
    setInterval(updateDateTime, 1000);
    updateDateTime();
});
