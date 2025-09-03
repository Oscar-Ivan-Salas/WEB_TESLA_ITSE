# Stop any running Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Remove existing virtual environment if it exists
$venvPath = ".\.venv"
if (Test-Path $venvPath) {
    Remove-Item -Recurse -Force $venvPath
    Write-Host "Removed existing virtual environment"
}

# Create new virtual environment
Write-Host "Creating new virtual environment..."
& python -m venv $venvPath

# Activate virtual environment
$activateScript = "$PWD\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Failed to create virtual environment. Activate script not found at: $activateScript"
}

Write-Host "Activating virtual environment..."
. $activateScript

# Upgrade pip and install dependencies
Write-Host "Upgrading pip and installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install fastapi==0.115.2 uvicorn pydantic==2.8.2 sqlalchemy==2.0.32 httpx python-dotenv

# Create secrets directory if it doesn't exist
$secretsDir = "$PWD\secrets"
if (-not (Test-Path $secretsDir)) {
    New-Item -ItemType Directory -Path $secretsDir | Out-Null
    Write-Host "Created secrets directory at: $secretsDir"
}

# Create .env file if it doesn't exist
$envFile = "$secretsDir\.env"
if (-not (Test-Path $envFile)) {
    @"
# API Configuration
OPENAI_API_KEY=your-api-key-here

# Database Configuration
DATABASE_URL=sqlite:///./sql_app.db
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Host "Created .env file at: $envFile"
}

Write-Host "`nEnvironment setup complete!"
Write-Host "To activate the virtual environment, run:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "`nTo start the FastAPI server, run:"
Write-Host "  uvicorn backend.app.main:app --reload"
