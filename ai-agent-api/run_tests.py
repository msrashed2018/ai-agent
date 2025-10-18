"""Test runner script for AI-Agent-API-Service test suite."""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the complete test suite with coverage."""
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    
    print("🧪 Running AI-Agent-API-Service Test Suite")
    print("=" * 50)
    
    # Test commands to run
    test_commands = [
        # Unit tests
        {
            "name": "Unit Tests",
            "command": [
                "python", "-m", "pytest",
                "tests/unit/",
                "-v",
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "-x",  # Stop on first failure
            ]
        },
        
        # Integration tests
        {
            "name": "Integration Tests",
            "command": [
                "python", "-m", "pytest",
                "tests/integration/",
                "-v",
                "-x",
            ]
        },
        
        # End-to-end tests
        {
            "name": "End-to-End Tests",
            "command": [
                "python", "-m", "pytest",
                "tests/e2e/",
                "-v",
                "-x",
            ]
        },
        
        # All tests with coverage
        {
            "name": "Full Test Suite",
            "command": [
                "python", "-m", "pytest",
                "tests/",
                "-v",
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-fail-under=80",  # Require 80% coverage
            ]
        },
    ]
    
    results = {}
    
    for test_config in test_commands:
        print(f"\n📋 Running {test_config['name']}...")
        print("-" * 30)
        
        try:
            result = subprocess.run(
                test_config["command"],
                cwd=project_root,
                check=True,
                capture_output=False,  # Show output in real-time
            )
            results[test_config["name"]] = "✅ PASSED"
            print(f"✅ {test_config['name']} completed successfully")
            
        except subprocess.CalledProcessError as e:
            results[test_config["name"]] = f"❌ FAILED (exit code {e.returncode})"
            print(f"❌ {test_config['name']} failed with exit code {e.returncode}")
            
            # For debugging, continue with other tests instead of stopping
            continue
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        print(f"{result} {test_name}")
    
    # Check if all tests passed
    failed_tests = [name for name, result in results.items() if "FAILED" in result]
    
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test suite(s) failed:")
        for test_name in failed_tests:
            print(f"   - {test_name}")
        return 1
    else:
        print(f"\n🎉 All {len(results)} test suites passed!")
        return 0


def run_specific_test(test_path: str):
    """Run a specific test file or directory."""
    
    print(f"🧪 Running specific test: {test_path}")
    
    command = [
        "python", "-m", "pytest",
        test_path,
        "-v",
        "-s",  # Don't capture output
        "--tb=short",  # Shorter traceback format
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"✅ Test {test_path} passed")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Test {test_path} failed with exit code {e.returncode}")
        return e.returncode


def run_with_coverage_only():
    """Run tests with detailed coverage report."""
    
    print("📊 Running tests with coverage analysis...")
    
    command = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "-q",  # Quiet mode
    ]
    
    try:
        subprocess.run(command, check=True)
        print("✅ Coverage report generated")
        print("📁 HTML report: htmlcov/index.html")
        print("📁 XML report: coverage.xml")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Coverage analysis failed with exit code {e.returncode}")
        return e.returncode


def check_test_dependencies():
    """Check if all test dependencies are installed."""
    
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-mock",
        "httpx",
        "fastapi",
        "sqlalchemy",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing test dependencies:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: poetry install --with dev")
        return False
    
    print("✅ All test dependencies are installed")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Agent-API Test Runner")
    parser.add_argument(
        "--test", "-t",
        help="Run specific test file or directory",
    )
    parser.add_argument(
        "--coverage-only", "-c",
        action="store_true",
        help="Run tests with coverage analysis only",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if test dependencies are installed",
    )
    
    args = parser.parse_args()
    
    if args.check_deps:
        sys.exit(0 if check_test_dependencies() else 1)
    
    if args.test:
        sys.exit(run_specific_test(args.test))
    
    if args.coverage_only:
        sys.exit(run_with_coverage_only())
    
    # Default: run full test suite
    sys.exit(run_tests())