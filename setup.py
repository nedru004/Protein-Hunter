#!/usr/bin/env python
"""
Complete setup.py for ProteinHunter - One-command installation
Handles all dependencies and post-install setup automatically
"""

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from pathlib import Path
import subprocess
import sys
import os

# Read README for long description
README = Path(__file__).parent / "README.md"
long_description = README.read_text(encoding="utf-8") if README.exists() else "ProteinHunter - Boltz Design Environment"

# Package metadata
PACKAGE_NAME = "proteinhunter"
VERSION = "1.0.0"
DESCRIPTION = "Protein Hunter"
AUTHOR = "Yehlin Cho"
AUTHOR_EMAIL = "yehlin@mit.edu"
URL = "https://github.com/yehlincho/Protein-Hunter"
PYTHON_REQUIRES = ">=3.10,<3.11"

# Core dependencies (from your pip install commands)
INSTALL_REQUIRES = [
    "matplotlib",
    "seaborn",
    "prody",
    "tqdm",
    "PyYAML",
    "requests",
    "pypdb",
    "py3Dmol",
    "logmd==0.1.45",
    "ml_collections",
    "numpy>=1.24,<1.27",  # Fixed version for compatibility
    "numba",
    "ipykernel",
]

# PyRosetta dependencies (optional due to licensing)
PYROSETTA_REQUIRES = [
    "pyrosettacolabsetup",
    "pyrosetta-installer",
]

# Optional dependencies
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
    ],
    "notebooks": [
        "jupyter>=1.0.0",
        "jupyterlab>=3.6.0",
    ],
    "pyrosetta": PYROSETTA_REQUIRES,
}

EXTRAS_REQUIRE["all"] = sum(EXTRAS_REQUIRE.values(), [])


class PostInstallCommand:
    """Handles all post-installation setup from your bash script"""
    
    @staticmethod
    def run_command(cmd, cwd=None, check=True):
        """Helper to run shell commands"""
        try:
            result = subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Command failed: {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return False
    
    @staticmethod
    def install_boltz_package():
        """Install boltz package if directory exists"""
        boltz_dir = Path("boltz")
        if boltz_dir.exists() and (boltz_dir / "setup.py").exists():
            print("📂 Installing Boltz package...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", "."],
                    cwd=boltz_dir,
                    check=True
                )
                print("✅ Boltz package installed")
                return True
            except Exception as e:
                print(f"⚠️  Warning: Failed to install Boltz package: {e}")
                return False
        else:
            print("ℹ️  Boltz directory not found or missing setup.py")
            return False
    
    @staticmethod
    def fix_numpy_numba():
        """Fix NumPy + Numba compatibility (PyRosetta downgrades NumPy to 1.23)"""
        print("🩹 Fixing NumPy/Numba version for Boltz and diffusion...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", 
                 "numpy>=1.24,<1.27", "numba"],
                check=True
            )
            print("✅ NumPy/Numba versions fixed")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Failed to fix NumPy/Numba: {e}")
            return False
    
    @staticmethod
    def download_boltz_weights():
        """Download Boltz weights and dependencies"""
        print("⬇️  Downloading Boltz weights and dependencies...")
        try:
            # Import here to avoid circular dependency
            from boltz.main import download_boltz2
            
            cache = Path.home() / ".boltz"
            cache.mkdir(parents=True, exist_ok=True)
            download_boltz2(cache)
            print("✅ Boltz weights downloaded successfully!")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Failed to download Boltz weights: {e}")
            print("You can download them manually later by running:")
            print("python -c 'from boltz.main import download_boltz2; from pathlib import Path; download_boltz2(Path.home() / \".boltz\")'")
            return False
    
    @staticmethod
    def setup_ligandmpnn():
        """Setup LigandMPNN if directory exists"""
        ligandmpnn_dir = Path("LigandMPNN")
        if ligandmpnn_dir.exists():
            print("🧬 Setting up LigandMPNN...")
            script_path = ligandmpnn_dir / "get_model_params.sh"
            if script_path.exists():
                try:
                    subprocess.run(
                        ["bash", "get_model_params.sh", "./model_params"],
                        cwd=ligandmpnn_dir,
                        check=True
                    )
                    print("✅ LigandMPNN setup complete")
                    return True
                except Exception as e:
                    print(f"⚠️  Warning: Failed to setup LigandMPNN: {e}")
                    return False
            else:
                print(f"⚠️  get_model_params.sh not found in {ligandmpnn_dir}")
                return False
        else:
            print("ℹ️  LigandMPNN directory not found, skipping...")
            return True
    
    @staticmethod
    def setup_dalpha_ball():
        """Make DAlphaBall.gcc executable"""
        print("🔧 Setting up DAlphaBall...")
        dalpha_path = Path("boltz/utils/DAlphaBall.gcc")
        if dalpha_path.exists():
            try:
                dalpha_path.chmod(0o755)
                print("✅ DAlphaBall.gcc is now executable")
                return True
            except Exception as e:
                print(f"⚠️  Warning: Failed to make DAlphaBall.gcc executable: {e}")
                return False
        else:
            print(f"ℹ️  DAlphaBall.gcc not found at {dalpha_path}")
            return False
    
    @staticmethod
    def setup_jupyter_kernel():
        """Setup Jupyter kernel for the environment"""
        print("📓 Setting up Jupyter kernel...")
        try:
            subprocess.run(
                [
                    sys.executable, "-m", "ipykernel", "install",
                    "--user",
                    "--name=boltz_ph",
                    "--display-name=Boltz Protein Hunter"
                ],
                check=True
            )
            print("✅ Jupyter kernel 'Boltz Protein Hunter' installed")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Failed to setup Jupyter kernel: {e}")
            print("You can set it up manually later with:")
            print("python -m ipykernel install --user --name=boltz_ph --display-name='Boltz Protein Hunter'")
            return False
    
    @staticmethod
    def install_pyrosetta(interactive=True):
        """Install PyRosetta with user confirmation"""
        print("\n" + "="*60)
        print("⏳ PyRosetta Installation")
        print("="*60)
        
        if interactive:
            print("PyRosetta requires acceptance of a license agreement.")
            print("Visit: https://www.pyrosetta.org/downloads")
            print("\nThis may take a while...")
            
            response = input("\nInstall PyRosetta now? (y/N): ").strip().lower()
            if response != 'y':
                print("ℹ️  Skipping PyRosetta installation.")
                print("To install later, run:")
                print("  pip install proteinhunter[pyrosetta]")
                print("  python -c 'import pyrosetta_installer; pyrosetta_installer.install_pyrosetta()'")
                return False
        
        try:
            print("Installing PyRosetta packages...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + PYROSETTA_REQUIRES,
                check=True
            )
            
            print("Running PyRosetta installer (this may take several minutes)...")
            subprocess.run(
                [sys.executable, "-c",
                 "import pyrosetta_installer; pyrosetta_installer.install_pyrosetta()"],
                check=True
            )
            
            # Fix NumPy after PyRosetta installation
            PostInstallCommand.fix_numpy_numba()
            
            print("✅ PyRosetta installed successfully!")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Failed to install PyRosetta: {e}")
            print("You can install it manually later.")
            return False
    
    @classmethod
    def run_all_setup(cls, include_pyrosetta=True, interactive=True):
        """Run all post-installation steps"""
        print("\n" + "="*60)
        print("🚀 Running ProteinHunter Post-Installation Setup")
        print("="*60 + "\n")
        
        results = {}
        
        # Step 1: Install Boltz package
        results['boltz'] = cls.install_boltz_package()
        
        # Step 2: Setup DAlphaBall
        results['dalpha'] = cls.setup_dalpha_ball()
        
        # Step 3: Setup LigandMPNN
        results['ligandmpnn'] = cls.setup_ligandmpnn()
        
        # Step 4: Download Boltz weights
        results['weights'] = cls.download_boltz_weights()
        
        # Step 5: Setup Jupyter kernel
        results['jupyter'] = cls.setup_jupyter_kernel()
        
        # Step 6: Install PyRosetta (optional)
        if include_pyrosetta:
            results['pyrosetta'] = cls.install_pyrosetta(interactive=interactive)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 Installation Summary")
        print("="*60)
        
        for step, success in results.items():
            status = "✅" if success else "⚠️ "
            print(f"{status} {step.capitalize()}: {'Success' if success else 'Skipped/Failed'}")
        
        print("\n" + "="*60)
        print("🎉 ProteinHunter Setup Complete!")
        print("="*60)
        
        print("\n📖 Next Steps:")
        print("  1. Run setup command:")
        print("     proteinhunter-setup")
        print("  2. Or verify installation:")
        print("     python -c 'import boltz; print(\"ProteinHunter ready!\")'")
        print("  3. Start using Jupyter:")
        print("     jupyter notebook")
        print("     (Select kernel: 'Boltz Protein Hunter')")
        print("  4. Check documentation:")
        print("     python -c 'from boltz import __doc__; print(__doc__)'")
        
        if not results.get('pyrosetta', True):
            print("\n💡 To install PyRosetta later:")
            print("  pip install proteinhunter[pyrosetta]")
            print("  python -c 'import pyrosetta_installer; pyrosetta_installer.install_pyrosetta()'")


class PostDevelopCommand(develop):
    """Post-installation for development mode"""
    def run(self):
        develop.run(self)
        print("\n🔧 Running post-installation setup for development mode...")
        PostInstallCommand.run_all_setup(include_pyrosetta=False, interactive=False)
        print("\n💡 To complete setup, run: proteinhunter-setup")


class PostInstallCommandWrapper(install):
    """Post-installation for normal install"""
    def run(self):
        install.run(self)
        # Show post-install message
        print("\n" + "="*60)
        print("✅ ProteinHunter base installation complete!")
        print("="*60)
        print("\n⚠️  IMPORTANT: Run post-installation setup:")
        print("  proteinhunter-setup")
        print("\nThis will:")
        print("  • Download Boltz model weights")
        print("  • Setup DAlphaBall executable")
        print("  • Configure Jupyter kernel")
        print("  • Setup LigandMPNN (if present)")
        print("  • Optionally install PyRosetta")
        print("\nOr run specific setup:")
        print("  proteinhunter-setup --weights-only    # Just download weights")
        print("  proteinhunter-setup --no-pyrosetta    # Skip PyRosetta")
        print("  proteinhunter-setup --jupyter-kernel  # Just Jupyter kernel")
        print("="*60 + "\n")


# Main setup configuration
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),
    include_package_data=True,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommandWrapper,
    },
    entry_points={
        "console_scripts": [
            "proteinhunter-setup=setup:cli_main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="protein structure prediction design bioinformatics boltz AI deep-learning",
    project_urls={
        "Bug Reports": f"{URL}/issues",
        "Source": URL,
        "Documentation": f"{URL}#readme",
    },
    zip_safe=False,
)


def main():
    """Entry point for manual post-installation setup"""
    PostInstallCommand.run_all_setup(include_pyrosetta=True, interactive=True)


def cli_main():
    """CLI entry point with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="ProteinHunter - Post-installation setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  proteinhunter-setup                    # Run full setup with prompts
  proteinhunter-setup --no-pyrosetta     # Skip PyRosetta installation
  proteinhunter-setup --non-interactive  # Run without prompts
  proteinhunter-setup --weights-only     # Only download Boltz weights
        """
    )
    
    parser.add_argument(
        '--no-pyrosetta',
        action='store_true',
        help='Skip PyRosetta installation'
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run setup without interactive prompts'
    )
    
    parser.add_argument(
        '--weights-only',
        action='store_true',
        help='Only download Boltz model weights'
    )
    
    parser.add_argument(
        '--jupyter-kernel',
        action='store_true',
        help='Only setup Jupyter kernel'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='ProteinHunter 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Handle specific commands
    if args.weights_only:
        print("⬇️  Downloading Boltz weights only...")
        PostInstallCommand.download_boltz_weights()
        return
    
    if args.jupyter_kernel:
        print("📓 Setting up Jupyter kernel only...")
        PostInstallCommand.setup_jupyter_kernel()
        return
    
    # Run full setup
    include_pyrosetta = not args.no_pyrosetta
    interactive = not args.non_interactive
    
    PostInstallCommand.run_all_setup(
        include_pyrosetta=include_pyrosetta,
        interactive=interactive
    )


if __name__ == "__main__":
    main()