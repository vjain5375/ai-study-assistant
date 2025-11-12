"""Setup script for the Study Assistant"""
import os
import subprocess
import sys

def create_directories():
    """Create necessary directories"""
    directories = ['outputs', 'uploads']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            print("⚠️  .env file not found. Creating from env.example...")
            with open('env.example', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print("✅ Created .env file. Please add your OpenAI API key!")
        else:
            print("⚠️  .env file not found. Please create one with your OpenAI API key.")
    else:
        print("✅ .env file exists")

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error installing requirements. Please run: pip install -r requirements.txt")

def main():
    """Main setup function"""
    print("🚀 Setting up AI Study Assistant...\n")
    
    create_directories()
    print()
    check_env_file()
    print()
    install_requirements()
    
    print("\n✨ Setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run: python main.py")
    print("   Or: streamlit run ui/app.py")

if __name__ == "__main__":
    main()

