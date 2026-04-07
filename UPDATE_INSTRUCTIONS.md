# CRITICAL FIX REQUIRED

The error `404 NOT FOUND` for `gemini-1.5-flash` is happening because specific Python libraries are outdated and locked by the running server.

**Please perform these steps exactly:**

1.  **Stop the running server**:
    If you have a terminal window running `uvicorn app.main:app...`, click in it and press `Ctrl+C` to stop it.

2.  **Run the update script**:
    In your terminal, run:
    ```cmd
    scripts\update_libs.bat
    ```
    (Or double-click the file in File Explorer)

3.  **Restart the server**:
    Once the update completes successfully, run:
    ```bash
    uvicorn app.main:app --reload --app-dir backend
    ```

After these steps, the `gemini-1.5-flash` model will work correctly.
