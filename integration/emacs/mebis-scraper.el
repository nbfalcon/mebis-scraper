;;; mebis-scraper.el --- mebis-scraper org-mode -*- lexical-binding: t -*-

;;; Commentary:
;; Implements functions to export completed tasks to an overlay file which can
;; be used with tools/patch_overlay.py. This way, tasks can be completed in
;; org-mode. That way, one's completed tasks can be remembered when regenerating
;; the tasks.org file and even, if desired, synchronized with mebis.

;;; Code:

(require 'org-element)
(require 'json)

(defun mebis-scraper--title-lineage (headline)
  "Return HEADLINE's and its parents' titles.
HEADLINE shall be an org-element headline."
  (delq nil (mapcar (apply-partially #'org-element-property :title)
                    (org-element-lineage headline))))

(defun mebis-scraper--parse-link (link)
  "Get the content ([[][CONTENT]]) from LINK.
LINK must be a string."
  (save-match-data
    (string-match "\\`\\[\\[\\([^z-a]*\\)\\]\\[\\([^z-a]*\\)\\]\\]\\'" link)
    (cons (match-string 1) (match-string 2))))

(defun mebis-scraper-element-to-locator (headline)
  "Return a completion-overlay locator alist for HEADLINE.
HEADLINE must be an org-element headline."
  (let ((parents (mebis-scraper--title-lineage headline))
        (activity (mebis-scraper--parse-link
                   (cdr (org-element-property :title headline)))))
    (cons
     (cons "name" activity)
     (pcase parents
       (`(,course ,subject)
        `(("course" . ,course)
          ("subject" . ,subject)))
       (`(,course ,subcourse ,subject)
        `(("course" . ,course)
          ("subcourse" . ,subcourse)
          ("subject" . ,subject)))))))

(defun mebis-scraper--completion-time (headline)
  "Return the time that HEADLINE was completed, or nil.
The time returned is the original CLOSED timestamp, as a string."
  (when-let ((complete-time (org-element-property :closed headline)))
    (org-element-property :raw-value (org-element-property :closed headline))))

(defun mebis-scraper--done-p (headline)
  "Test whether HEADLINE is completed or not.
Return t if it is and `:json-false' if it is not (!)."
  (if (eq (org-element-property :todo-type headline) 'done) t :json-false))

(defun mebis-scraper-element-to-complete (headline)
  "Return an alist specifiying HEADLINE's completion.
Its complete property holds (as a json boolean) wether HEADLINE
is completed and its completed property holds the completion
time (as an org-timestamp string)."
  `(("complete" . ,(mebis-scraper--done-p headline))
    ("completed" . ,(mebis-scraper--completion-time headline))))

(defun mebis-scraper-ast-to-complete-overlay (ast)
  "Return a completion-overlay json-tree from AST.
AST must be an org-element tree obtained using
`org-element-parse-buffer'."
  (org-element-map ast 'headline
    (lambda (headline)
      ;; is a todo?
      (when (org-element-property :todo-keyword headline)
        (nconc (mebis-scraper-element-to-locator headline)
               (mebis-scraper-element-to-complete headline))))))

(defun mebis-scraper-buffer-to-complete-overlay ()
  "Generate and return a completion overlay from the current org buffer.
The buffer must have been obtained using coursedump2org.py."
  (mebis-scraper-ast-to-complete-overlay (org-element-parse-buffer 'headline)))

(define-minor-mode mebis-scraper-tasks-export-mode
  "Export the tasks buffer on every save."
  :init-value nil
  :lighter nil
  (if mebis-scraper-tasks-export-mode
      (add-hook 'after-save-hook #'mebis-scraper-export nil t)
    (remove-hook 'after-save-hook #'mebis-scraper-export t)))

(defcustom mebis-scraper-todo-export-file nil
  "Specify the path to the completion overlay.
This file will hold the completion states of your tasks."
  :group 'mebis-scraper
  :type 'file)

(defcustom mebis-scraper-tasks-file nil
  "Specify the location of your tasks.org file.
This file will be opened by `mebis-scraper-open-tasks-file'."
  :group 'mebis-scraper
  :type 'file)

(defun mebis-scraper-export ()
  "Export the current buffer to `mebis-scraper-todo-export-file'."
  (interactive)
  (write-region (json-encode (mebis-scraper-buffer-to-complete-overlay))
                nil mebis-scraper-todo-export-file))

(defun mebis-scraper-open-tasks-buffer ()
  "Open `mebis-scraper-tasks-file' with export after save enabled."
  (interactive)
  (find-file mebis-scraper-tasks-file)
  (mebis-scraper-tasks-export-mode 1))

(defun mebis-scraper-open-tasks-buffer-noselect ()
  "Open the mebis-scraper tasks.org file in the background."
  (with-current-buffer (find-file-noselect mebis-scraper-tasks-file)
    (mebis-scraper-tasks-export-mode 1)))

(provide 'mebis-scraper)
;;; mebis-scraper.el ends here
