/**
 * LMS - Library Management System
 * Main Application JavaScript
 */

function initApp() {
  'use strict';

  // =============================================
  // SIDEBAR TOGGLE (Non-member / Desktop)
  // =============================================
  var menuToggle = document.getElementById('menuToggle');
  var sidebar = document.querySelector('.sidebar');
  var sidebarOverlay = document.getElementById('sidebarOverlay');
  var lmsWrapper = document.querySelector('.lms-wrapper');

  if (menuToggle && sidebar) {
    menuToggle.onclick = function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
        if (sidebarOverlay) sidebarOverlay.classList.toggle('show');
      } else {
        if (lmsWrapper) lmsWrapper.classList.toggle('sidebar-collapsed');
      }
    };
  }

  if (sidebarOverlay) {
    sidebarOverlay.onclick = function() {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('show');
    };
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
        setTimeout(function() { alert.remove(); }, 300);
      }
    });
  });

  setTimeout(function() {
    document.querySelectorAll('.alert').forEach(function(alert) {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(function() { if (alert.parentNode) alert.remove(); }, 300);
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

  document.querySelectorAll('[data-modal-close]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var modal = btn.closest('.modal-overlay');
      if (modal) modal.classList.remove('show');
    });
  });

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
  var userDropdown = document.getElementById('userDropdown');

  if (notifBtn && notifDropdown) {
    notifBtn.onclick = function(e) {
      e.stopPropagation();
      var isShowing = notifDropdown.classList.contains('show');
      if (userDropdown) userDropdown.classList.remove('show');
      notifDropdown.classList.toggle('show');

      if (!isShowing) {
        var dot = notifBtn.querySelector('.notification-dot, .notif-badge');
        if (dot) {
          fetch('/notifications/read', { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function(d) {
              if (d.status === 'success') dot.style.display = 'none';
            })
            .catch(function() {});
        }
      }
    };
  }

  // =============================================
  // USER PROFILE DROPDOWN
  // =============================================
  var userMenuBtn = document.getElementById('userMenuBtn');
  userDropdown = document.getElementById('userDropdown');

  if (userMenuBtn && userDropdown) {
    userMenuBtn.onclick = function(e) {
      e.stopPropagation();
      if (notifDropdown) notifDropdown.classList.remove('show');
      userDropdown.classList.toggle('show');
    };
  }

  // Close dropdowns on outside click (bind once, look up elements each time)
  if (!window._docClickBound) {
    document.addEventListener('click', function(e) {
      var nDrop = document.getElementById('notifDropdown');
      var uDrop = document.getElementById('userDropdown');
      var nBtn  = document.getElementById('notifBtn');
      var uBtn  = document.getElementById('userMenuBtn');
      if (nDrop && nBtn && !nBtn.contains(e.target) && !nDrop.contains(e.target)) {
        nDrop.classList.remove('show');
      }
      if (uDrop && uBtn && !uBtn.contains(e.target) && !uDrop.contains(e.target)) {
        uDrop.classList.remove('show');
      }
    });
    window._docClickBound = true;
  }

  // =============================================
  // MEMBER SEARCH POPUP (Dashboard search button)
  // =============================================
  var searchPopupBtn = document.getElementById('memberSearchPopupBtn');
  var searchPopup = document.getElementById('memberSearchPopup');
  var searchPopupInput = document.getElementById('memberSearchPopupInput');
  var searchPopupClose = document.getElementById('memberSearchPopupClose');

  if (searchPopupBtn && searchPopup) {
    searchPopupBtn.onclick = function(e) {
      e.preventDefault();
      e.stopPropagation();
      searchPopup.classList.add('show');
      if (searchPopupInput) setTimeout(function() { searchPopupInput.focus(); }, 100);
    };
  }
  if (searchPopupClose && searchPopup) {
    searchPopupClose.onclick = function() {
      searchPopup.classList.remove('show');
    };
  }
  if (searchPopup) {
    searchPopup.addEventListener('click', function(e) {
      if (e.target === searchPopup) searchPopup.classList.remove('show');
    });
  }
  if (searchPopupInput) {
    searchPopupInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        var q = searchPopupInput.value.trim();
        if (q) window.location.href = '/books?search=' + encodeURIComponent(q);
      }
      if (e.key === 'Escape') {
        if (searchPopup) searchPopup.classList.remove('show');
      }
    });
    // Live search results in popup
    var popupDebounce;
    var popupResults = document.getElementById('memberSearchPopupResults');
    searchPopupInput.addEventListener('input', function() {
      clearTimeout(popupDebounce);
      var q = searchPopupInput.value.trim();
      if (!popupResults) return;
      if (q.length < 2) { popupResults.innerHTML = ''; return; }
      popupDebounce = setTimeout(function() {
        fetch('/books/search?q=' + encodeURIComponent(q))
          .then(function(r) { return r.json(); })
          .then(function(data) {
            if (!data.length) {
              popupResults.innerHTML = '<div class="search-popup-item muted">No books found for "' + q + '"</div>';
            } else {
              popupResults.innerHTML = data.slice(0, 8).map(function(b) {
                var avail = b.available
                  ? '<span style="color:#27ae60; font-size:0.7rem;">Available</span>'
                  : '<span style="color:#e74c3c; font-size:0.7rem;">Unavailable</span>';
                return '<a href="/books/' + b.id + '" class="search-popup-item">' +
                  '<div style="font-weight:600; font-size:0.9rem;">' + b.title + '</div>' +
                  '<div style="font-size:0.75rem; color:#666;">by ' + b.author + '&nbsp;&nbsp;' + avail + '</div>' +
                  '</a>';
              }).join('');
            }
          })
          .catch(function() {});
      }, 250);
    });
  }

  // =============================================
  // TOPBAR SEARCH (Non-member / admin)
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
      memberDebounce = setTimeout(function() {
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
  // AUTO-CALCULATE DUE DATE
  // =============================================
  var issueDateInput = document.getElementById('issue_date');
  var dueDateInput = document.getElementById('due_date');
  var defaultDaysEl = document.getElementById('default_borrow_days');
  var defaultDays = parseInt(defaultDaysEl ? defaultDaysEl.value : '14');

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
  // AUTOCOMPLETE STYLES
  // =============================================
  if (!document.getElementById('_lms_autocomplete_style')) {
    var style = document.createElement('style');
    style.id = '_lms_autocomplete_style';
    style.textContent = [
      '.autocomplete-wrapper { position: relative; }',
      '.autocomplete-results { position:absolute; top:100%; left:0; right:0; background:white;',
      '  border:1px solid var(--border); border-radius:0 0 var(--radius) var(--radius);',
      '  box-shadow:var(--shadow-md); z-index:100; max-height:250px; overflow-y:auto; display:none; }',
      '.autocomplete-item { padding:0.65rem 0.875rem; cursor:pointer; font-size:0.875rem;',
      '  border-bottom:1px solid #f5f5f5; transition:background 0.15s; }',
      '.autocomplete-item:last-child { border-bottom:none; }',
      '.autocomplete-item:hover { background:#f0f4ff; }'
    ].join('\n');
    document.head.appendChild(style);
  }

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
  // TOOLTIPS
  // =============================================
  document.querySelectorAll('[title]').forEach(function(el) {
    el.setAttribute('data-bs-toggle', 'tooltip');
  });
}

// Run on normal page load AND on Turbo navigation
document.addEventListener('DOMContentLoaded', initApp);
document.addEventListener('turbo:load', initApp);

