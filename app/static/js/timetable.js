// Timetable management functions
function assignSubject(subjectId) {
    const teacherId = document.getElementById('teacherSelect').value;
    const classId = document.getElementById('classSelect').value;
    
    fetch('/timetable/assign_subject', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            subject_id: subjectId,
            teacher_id: teacherId,
            class_id: classId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
        } else {
            showAlert('success', 'Subject assigned successfully');
            location.reload();
        }
    })
    .catch(error => {
        showAlert('error', 'Failed to assign subject');
        console.error('Error:', error);
    });
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
}

// Handle notifications
function markNotificationAsRead(notificationId) {
    fetch(`/notifications/mark_read/${notificationId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.querySelector(`#notification-${notificationId}`).remove();
            updateNotificationCount();
        }
    });
}

function updateNotificationCount() {
    const count = document.querySelectorAll('.notification-item').length;
    const badge = document.querySelector('.notification-count');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

function generateTimetables() {
        const selectedClasses = Array.from(document.querySelectorAll('input[name="classes"]:checked'))
            .map(input => input.value);

        if (selectedClasses.length === 0) {
            alert('Please select at least one class');
            return;
        }

        const options = {
            optimizeTeacherLoad: document.getElementById('optimizeTeacherLoad').checked,
            avoidConsecutive: document.getElementById('avoidConsecutive').checked,
            distributeSubjects: document.getElementById('distributeSubjects').checked
        };

        // Show loading state
        const generateBtn = document.querySelector('#generateModal .btn-primary');
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generating...';
        generateBtn.disabled = true;

        // Make API call to generate timetables
        Promise.all(selectedClasses.map(classId =>
            fetch(/admin/timetable / ${ classId } / generate, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token() }}'
                },
                body: JSON.stringify(options)
            })
        )).then(() => {
            location.reload();
        }).catch(error => {
            alert('Failed to generate timetables. Please try again.');
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        });
    }