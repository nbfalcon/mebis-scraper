;; -*- mode: emacs-lisp; lexical-binding: t -*-
(require 'org-element)
(require 'json)

(defun org-element-get-parents (headline)
  (seq-filter
   (lambda (e) (not (null e)))
   (mapcar (lambda (hl) (org-element-property :title hl))
           (org-element-lineage headline))))

(defun org-element-is-todo (headline)
  (not (null (org-element-property :todo-keyword headline))))

(defun org-get-link-content (link)
  (replace-regexp-in-string "\\[\\[\\(.*\\)\\]\\[\\(.*\\)\\]\\]" "\\2" link))
(defun mebis-scraper-element-to-locator (headline)
  (let ((parents (org-element-get-parents headline))
        (activity (org-get-link-content
                   (org-element-property :title headline))))
    (cond ((eq (length parents) 2) ;; '(course subject)
           (list (cons "course" (nth 1 parents))
                 (cons "subject" (nth 0 parents))
                 (cons "name" activity)))
          ((eq (length parents) 3) ;; '(course subcourse subject)
           (list (cons "course" (nth 2 parents))
                 (cons "subcourse" (nth 1 parents))
                 (cons "subject" (nth 0 parents))
                 (cons "name" activity))))))

(defun org-todo-is-done (headline)
  (let ((type (org-element-property :todo-type headline)))
    (if (eq type 'done)
        t
      json-false)))

(defconst org-timestamp-format-string
  "%Y-%m-%d %a %H:%M")

(defun current-tz ()
  (nth 1 (current-time-zone)))

(defun org-completed-to-string (headline)
  (let ((complete-time (org-element-property :closed headline)))
    (if (null complete-time)
        nil
      (org-element-property
       :raw-value (org-element-property :closed headline)))))

(defun mebis-scraper-element-to-complete (headline)
  (list (cons "complete" (org-todo-is-done headline))
        (cons "completed" (org-completed-to-string headline))))

(defun mebis-scraper-ast-to-complete-overlay (ast)
  (org-element-map ast 'headline
    (lambda (headline)
      (if (org-element-is-todo headline)
          (nconc (mebis-scraper-element-to-locator headline)
                 (mebis-scraper-element-to-complete headline))
        nil))))

(defun mebis-scraper-org-to-complete-overlay ()
  (mebis-scraper-ast-to-complete-overlay (org-element-parse-buffer 'headline)))

(define-minor-mode mebis-scraper-tasks-export-mode
  "Export the tasks buffer on every save."
  :init-value nil
  :lighter nil
  (if mebis-scraper-tasks-export-mode
      (add-hook 'after-save-hook #'mebis-scraper-export nil t)
    (remove-hook 'after-save-hook #'mebis-scraper-export t)))

(defcustom mebis-scraper-todo-export-file nil
  "This variable specifies the json file to which the completion
overlay will be written when invoking `mebis-scraper-export'."
  :group 'mebis-scraper
  :type 'file)

(defcustom mebis-scraper-tasks-file nil
  "When invoking `mebis-scraper-open-tasks-buffer', the file
specified by this variable will be opened."
  :group 'mebis-scraper
  :type 'file)

(defun mebis-scraper-export ()
  (interactive)
  (write-region (json-encode (mebis-scraper-org-to-complete-overlay))
                nil mebis-scraper-todo-export-file))

(defun mebis-scraper-open-tasks-buffer ()
  "Opens the org file containing the mebis tasks to do."
  (interactive)
  (find-file mebis-scraper-tasks-file)
  (mebis-scraper-tasks-export-mode 1))

(provide 'mebis-scraper)
