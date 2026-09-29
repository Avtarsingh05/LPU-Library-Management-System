/**
 * LMS - Library Management System
 * Main Application JavaScript
 */

function initApp() {
  'use strict';

  // =============================================
  // SIDEBAR TOGGLE (Mobile)
  // =============================================
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.querySelector('.sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  const lmsWrapper = document.querySelector('.lms-wrapper');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
        if (sidebarOverlay) sidebarOverlay.classList.toggle('show');
      } else {
        if (lmsWrapper) lmsWrapper.classList.toggle('sidebar-collapsed');
      }
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', function() {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('show');
    });
  }

  // =============================================
  // FLASH MESSAGE DISMISS
  // =============================================
  document.querySelectorAll('.alert-close').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        alert.style.transition = 'all 0.3s ease';
        setTimeoutfunction initApp() { alert.remove(); }, 300);
      }
    });
  });

  // Auto-dismiss flash messages after 5 seconds
  setTimeoutfunction initApp() {
    document.querySelectorAll('.alert').forEach(function(alert) {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeoutfunction initApp() { if (alert.parentNode) alert.remove(); }, 300);
    });
  }, 5000);

  // =============================================
  // DELETE CONFIRMATION MODAL
  // =============================================
  var deleteModal = document.getElementById('deleteModal');
  var deleteForm = document.getElementById('deleteForm');
  var deleteItemName = document.getElementById('deleteItemName');

  document.querySelectorAll('[data-delete-url]').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      var url = btn.getAttribute('data-delete-url');
      var name = btn.getAttribute('data-item-name') || 'this item';
      if (deleteModal && deleteForm) {
        deleteForm.action = url;
        if (deleteItemName) deleteItemName.textContent = name;
        deleteModal.classList.add('show');
      }
    });
  });

  // Close modal
  document.querySelectorAll('[data-modal-close]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var modal = btn.closest('.modal-overlay');
      if (modal) modal.classList.remove('show');
    });
  });

  // Close modal on overlay click
  document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.classList.remove('show');
    });
  });

  // =============================================
  // NOTIFICATION DROPDOWN
  // =============================================
  var notifBtn = document.getElementById('notifBtn');
  var notifDropdown = document.getElementById('notifDropdown');

  if (notifBtn && notifDropdown) {
    notifBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      var isShowing = notifDropdown.classList.contains('show');
      if (userDropdown) userDropdown.classList.remove('show');
      notifDropdown.classList.toggle('show');
      
      if (!isShowing) {
        var dot = notifBtn.querySelector('.notification-dot');
        if (dot) {
          fetch('/notifications/read', { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function(d) {
              if (d.status === 'success') {
                dot.style.display = 'none';
              }
            })
            .catch(function(e) { console.error(e); });
        }
      }
    });
  }

  // =============================================
  // USER PROFILE DROPDOWN
  // =============================================
  var userMenuBtn = document.getElementById('userMenuBtn');
  var userDropdown = document.getElementById('userDropdown');

  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });
  }

  // Close dropdowns on outside click
  document.addEventListener('click', function(e) {
    if (notifBtn && notifDropdown && !notifBtn.contains(e.target) && !notifDropdown.contains(e.target)) {
      notifDropdown.classList.remove('show');
    }
    if (userMenuBtn && userDropdown && !userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
      userDropdown.classList.remove('show');
    }
  });

  // =============================================
  // LIVE MEMBER SEARCH (Issue Book page)
  // =============================================
  var memberSearch = document.getElementById('memberSearch');
  var memberResults = document.getElementById('memberResults');
  var memberIdInput = document.getElementById('member_id');

  if (memberSearch) {
    var memberDebounce;
    memberSearch.addEventListener('input', function() {
      clearTimeout(memberDebounce);
      var q = memberSearch.value.trim();
      if (!memberResults) return;
      if (q.length < 2) { memberResults.innerHTML = ''; memberResults.style.display = 'none'; return; }
      
      memberDebounce = setTimeoutfunction initApp() {
        fetch('/members/search?q=' + encodeURIComponent(q))
          .then(function(r) { return r.json(); })
          .then(function(data) {
            if (!data.length) {
              memberResults.innerHTML = '<div class="autocomplete-item text-muted">No members found</div>';
            } else {
              memberResults.innerHTML = data.map(function(m) {
                return '<div class="autocomplete-item" data-id="' + m.id + '" data-name="' + m.name + '">' +
                  '<strong>' + m.name + '</strong> <span class="text-muted">' + m.member_id + '</span>' +
                  '<small class="d-block text-muted">' + m.email + ' | Active Issues: ' + m.active_issues + '</small>' +
                  '</div>';
              }).join('');
            }
            memberResults.style.display = 'block';

            memberResults.querySelectorAll('.autocomplete-item[data-id]').forEach(function(item) {
              item.addEventListener('click', function() {
                memberSearch.value = item.dataset.name;
                if (memberIdInput) memberIdInput.value = item.dataset.id;
                memberResults.style.display = 'none';
              });
            });
          });
      }, 300);
    });
  }

  // =============================================
  // LIVE BOOK SEARCH (Issue Book page)
  // =============================================
  var bookSearch = document.getElementById('bookSearch');
  var bookResults = document.getElementById('bookResults');
  var bookIdInput = document.getElementById('book_id');
  var bookAvailability = document.getElementById('bookAvailability');

  if (bookSearch) {
    var bookDebounce;
    bookSearch.addEventListener('input', function() {
      clearTimeout(bookDebounce);
      var q = bookSearch.value.trim();
      if (!bookResults) return;
      if (q.length < 2) { bookResults.innerHTML = ''; bookResults.style.display = 'none'; return; }
      
      bookDebounce = setTimeoutfunction initApp() {
        fetch('/books/search?q=' + encodeURIComponent(q))
          .then(function(r) { return r.json(); })
          .then(function(data) {
            if (!data.length) {
              bookResults.innerHTML = '<div class="autocomplete-item text-muted">No books found</div>';
            } else {
              bookResults.innerHTML = data.map(function(b) {
                var avail = b.available ? 
                  '<span class="badge badge-success">' + b.available_copies + ' available</span>' :
                  '<span class="badge badge-danger">Not available</span>';
                return '<div class="autocomplete-item" data-id="' + b.id + '" data-name="' + b.title + '" data-available="' + b.available + '">' +
                  '<strong>' + b.title + '</strong> ' + avail +
                  '<small class="d-block text-muted">by ' + b.author + ' | ISBN: ' + b.isbn + '</small>' +
                  '</div>';
              }).join('');
            }
            bookResults.style.display = 'block';

            bookResults.querySelectorAll('.autocomplete-item[data-id]').forEach(function(item) {
              item.addEventListener('click', function() {
                bookSearch.value = item.dataset.name;
                if (bookIdInput) bookIdInput.value = item.dataset.id;
                bookResults.style.display = 'none';
                if (bookAvailability) {
                  if (item.dataset.available === 'True' || item.dataset.available === 'true') {
                    bookAvailability.innerHTML = '<div class="alert alert-success"><i class="bi bi-check-circle"></i> Book is available for issuing</div>';
                  } else {
                    bookAvailability.innerHTML = '<div class="alert alert-danger"><i class="bi bi-x-circle"></i> Book is not available</div>';
                    var issueBtn = document.getElementById('issueBtn');
                    if (issueBtn) issueBtn.disabled = true;
                  }
                }
              });
            });
          });
      }, 300);
    });
  }

  // =============================================
  // AUTO-CALCULATE DUE DATE
  // =============================================
  var issueDateInput = document.getElementById('issue_date');
  var dueDateInput = document.getElementById('due_date');
  var defaultDays = parseInt(document.getElementById('default_borrow_days')?.value || '14');

  if (issueDateInput && dueDateInput) {
    issueDateInput.addEventListener('change', function() {
      var issueDate = new Date(issueDateInput.value);
      if (!isNaN(issueDate)) {
        var dueDate = new Date(issueDate);
        dueDate.setDate(dueDate.getDate() + defaultDays);
        dueDateInput.value = dueDate.toISOString().split('T')[0];
      }
    });
  }

  // =============================================
  // TOPBAR SEARCH
  // =============================================
  var topbarSearchInput = document.getElementById('topbarSearch');
  if (topbarSearchInput) {
    topbarSearchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        var q = topbarSearchInput.value.trim();
        if (q) window.location.href = '/books?search=' + encodeURIComponent(q);
      }
    });
  }

  // =============================================
  // AUTOCOMPLETE STYLES (inline)
  // =============================================
  var style = document.createElement('style');
  style.textContent = `
    .autocomplete-wrapper { position: relative; }
    .autocomplete-results {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: white;
      border: 1px solid var(--border);
      border-radius: 0 0 var(--radius) var(--radius);
      box-shadow: var(--shadow-md);
      z-index: 100;
      max-height: 250px;
      overflow-y: auto;
      display: none;
    }
    .autocomplete-item {
      padding: 0.65rem 0.875rem;
      cursor: pointer;
      font-size: 0.875rem;
      border-bottom: 1px solid #f5f5f5;
      transition: background 0.15s;
    }
    .autocomplete-item:last-child { border-bottom: none; }
    .autocomplete-item:hover { background: #f0f4ff; }
  `;
  document.head.appendChild(style);

  // =============================================
  // PRINT FUNCTIONALITY
  // =============================================
  document.querySelectorAll('[data-action="print"]').forEach(function(btn) {
    btn.addEventListener('click', function() { window.print(); });
  });

  // =============================================
  // FORM VALIDATION
  // =============================================
  document.querySelectorAll('form[data-validate]').forEach(function(form) {
    form.addEventListener('submit', function(e) {
      var valid = true;
      form.querySelectorAll('[required]').forEach(function(field) {
        if (!field.value.trim()) {
          field.classList.add('is-invalid');
          valid = false;
        } else {
          field.classList.remove('is-invalid');
        }
      });
      if (!valid) e.preventDefault();
    });
  });

  // =============================================
  // ACTIVE SIDEBAR LINK
  // =============================================
  var currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(function(link) {
    var href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && (currentPath === '/' || currentPath === '/dashboard')) {
      link.classList.add('active');
    }
  });

  // =============================================
  // TOOLTIP INITIALIZATION
  // =============================================
  document.querySelectorAll('[title]').forEach(function(el) {
    el.setAttribute('data-bs-toggle', 'tooltip');
  });

} 

document.addEventListener('turbo:load', initApp);
document.addEventListener('DOMContentLoaded', initApp);

