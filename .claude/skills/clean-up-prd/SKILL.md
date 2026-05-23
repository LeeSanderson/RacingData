---
name: clean-up-prd
description: Verify all issues related to the current PRD have been completed and then delete all issues and the PRD itself to maintain a clean project management environment.
Use when user explicitly states "clean up PRD" or when a PRD has been marked as completed and needs to be archived.
---

Review the current PRD and all associated issues. Verify that all tasks related to the PRD have been completed successfully. If any issues are still open, provide a summary of the remaining tasks and ask the user if they would like to proceed with cleaning up the PRD or if they want to address the remaining issues first.

Assuming all issues are completed, proceed to delete all issues associated with the PRD. After confirming that all issues have been removed, delete the PRD itself.

Always wait for my approval before deleting any issues or the PRD.

After deleting the PRD and issues commit the changes to the repository with a clear commit message indicating that the PRD and associated issues have been cleaned up and the feature has been completed.
