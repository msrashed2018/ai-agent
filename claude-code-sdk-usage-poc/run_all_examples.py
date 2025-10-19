#!/usr/bin/env python3
"""
Run All Examples - Claude Agent SDK Test Suite

This script runs all example scripts in sequence to demonstrate
the full capabilities of the Claude Agent SDK.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path


def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    width = 70
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*20} {title} {'='*20}")


async def run_script(script_path: str, description: str):
    """Run a single example script."""
    print(f"🚀 Running: {script_path}")
    print(f"📝 Description: {description}")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Run the script
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=Path(script_path).parent
        )
        
        # Read output in real-time
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(line.decode().rstrip())
        
        # Wait for completion
        await process.wait()
        
        if process.returncode == 0:
            print("✅ Script completed successfully")
        else:
            print(f"❌ Script failed with exit code: {process.returncode}")
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False


async def run_all_examples():
    """Run all example scripts in sequence."""
    
    # Define all examples with descriptions
    examples = [
        {
            "script": "01_basic_hello_world.py",
            "description": "Basic usage with query() function and simple file operations",
            "interactive": False
        },
        {
            "script": "02_interactive_chat.py", 
            "description": "Interactive chat client with command support",
            "interactive": True
        },
        {
            "script": "03_custom_permissions.py",
            "description": "Custom permission handlers and security controls",
            "interactive": True
        },
        {
            "script": "04_hook_system.py",
            "description": "Event hooks for monitoring and controlling operations",
            "interactive": False
        },
        {
            "script": "05_mcp_sdk_servers.py",
            "description": "SDK MCP servers with custom tools and in-process execution",
            "interactive": False
        },
        {
            "script": "06_external_mcp_servers.py",
            "description": "External MCP server configuration and mixed server setups",
            "interactive": False
        },
        {
            "script": "07_advanced_streaming.py",
            "description": "Advanced streaming, interrupts, and session management",
            "interactive": False
        },
        {
            "script": "08_production_ready.py",
            "description": "Production-ready implementation with comprehensive error handling",
            "interactive": True
        }
    ]
    
    print_header("Claude Agent SDK - Complete Test Suite")
    
    print("🎯 This test suite demonstrates all features of the Claude Agent SDK:")
    print("   • Basic query() function usage")
    print("   • Interactive streaming client")
    print("   • Custom permission handling")
    print("   • Event hook system")
    print("   • SDK MCP server creation")
    print("   • External MCP server integration")
    print("   • Advanced streaming features")
    print("   • Production-ready patterns")
    print()
    
    # Check prerequisites
    print_section("Prerequisites Check")
    
    # Check if Claude Code is installed
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Claude Code installed: {result.stdout.strip()}")
        else:
            print("❌ Claude Code not found or not working")
            print("   Install with: npm install -g @anthropic-ai/claude-code")
            return
    except FileNotFoundError:
        print("❌ Claude Code not found in PATH")
        print("   Install with: npm install -g @anthropic-ai/claude-code")
        return
    
    # Check if all example files exist
    missing_files = []
    for example in examples:
        if not Path(example["script"]).exists():
            missing_files.append(example["script"])
    
    if missing_files:
        print(f"❌ Missing example files: {missing_files}")
        return
    
    print("✅ All prerequisites met")
    
    # Create output directories
    print_section("Setup")
    
    directories = ["./workspace", "./output", "./logs", "./temp"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Run examples
    successful = 0
    failed = 0
    
    for i, example in enumerate(examples, 1):
        print_section(f"Example {i}/{len(examples)}: {example['script']}")
        
        if example["interactive"]:
            print("⚠️  This example includes interactive components.")
            print("   Some prompts may require user input or may run for extended periods.")
            print("   Press Ctrl+C if you need to interrupt.")
            print()
            
            response = input("Continue with this example? (y/N): ")
            if response.lower() != 'y':
                print("⏭️  Skipping interactive example")
                continue
        
        start_time = time.time()
        success = await run_script(example["script"], example["description"])
        duration = time.time() - start_time
        
        if success:
            successful += 1
            print(f"✅ Completed in {duration:.1f} seconds")
        else:
            failed += 1
            print(f"❌ Failed after {duration:.1f} seconds")
        
        # Add delay between examples
        if i < len(examples):
            print("\n⏸️  Waiting 3 seconds before next example...")
            await asyncio.sleep(3)
    
    # Summary
    print_header("Test Suite Summary")
    
    total = successful + failed
    print(f"📊 Results:")
    print(f"   Total examples: {total}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Success rate: {(successful/total*100) if total > 0 else 0:.1f}%")
    
    if failed == 0:
        print("\n🎉 All examples completed successfully!")
        print("   The Claude Agent SDK is working correctly.")
    else:
        print(f"\n⚠️  {failed} examples failed.")
        print("   Check the output above for error details.")
        print("   Common issues:")
        print("   • Claude Code not properly installed")
        print("   • Missing API credentials")
        print("   • Network connectivity issues")
        print("   • Permission/security restrictions")
    
    print("\n📚 Next Steps:")
    print("   • Review the documentation files for detailed usage")
    print("   • Examine individual example scripts for specific patterns")
    print("   • Check the workspace/ directory for generated files")
    print("   • Look at logs/ directory for metrics and debugging info")


async def run_quick_test():
    """Run a quick test to verify basic functionality."""
    print_header("Quick Functionality Test")
    
    print("🔍 Running basic functionality test...")
    
    success = await run_script(
        "01_basic_hello_world.py",
        "Quick test of basic SDK functionality"
    )
    
    if success:
        print("\n✅ Quick test passed!")
        print("   The Claude Agent SDK appears to be working correctly.")
        print("   Run with --full to execute all examples.")
    else:
        print("\n❌ Quick test failed!")
        print("   Please check your Claude Code installation and configuration.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Agent SDK Test Suite")
    parser.add_argument("--full", action="store_true", help="Run all examples (may take time)")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    
    args = parser.parse_args()
    
    if args.full:
        asyncio.run(run_all_examples())
    elif args.quick:
        asyncio.run(run_quick_test())
    else:
        print("Claude Agent SDK Test Suite")
        print("Usage:")
        print("  python run_all_examples.py --quick    # Quick functionality test")
        print("  python run_all_examples.py --full     # Complete test suite")
        print()
        print("The complete test suite includes interactive examples that may")
        print("require user input and can take significant time to complete.")


if __name__ == "__main__":
    main()