// Dynamic filtering for admin forms
function filterDepartments(facultyId) {
    const departmentSelect = document.querySelector('select[name="department"]');
    const topicSelect = document.querySelector('select[name="topic"]');

    if (!departmentSelect) return;

    // Clear current options except the first (empty) one
    departmentSelect.innerHTML = '<option value="">---------</option>';
    topicSelect.innerHTML = '<option value="">---------</option>';

    if (facultyId) {
        // Fetch departments for the selected faculty
        fetch(`/admin/catalog/department/?faculty=${facultyId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.id;
                    option.textContent = dept.name;
                    departmentSelect.appendChild(option);
                });
            })
            .catch(error => console.error('Error fetching departments:', error));
    }
}

function filterTopics(departmentId) {
    const topicSelect = document.querySelector('select[name="topic"]');

    if (!topicSelect) return;

    // Clear current options except the first (empty) one
    topicSelect.innerHTML = '<option value="">---------</option>';

    if (departmentId) {
        // Fetch topics for the selected department
        fetch(`/admin/catalog/topic/?department=${departmentId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(topic => {
                    const option = document.createElement('option');
                    option.value = topic.id;
                    option.textContent = topic.name;
                    topicSelect.appendChild(option);
                });
            })
            .catch(error => console.error('Error fetching topics:', error));
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const facultySelect = document.querySelector('select[name="faculty"]');
    const departmentSelect = document.querySelector('select[name="department"]');

    if (facultySelect) {
        facultySelect.addEventListener('change', function() {
            filterDepartments(this.value);
        });
    }

    if (departmentSelect) {
        departmentSelect.addEventListener('change', function() {
            filterTopics(this.value);
        });
    }
});
