#!/usr/bin/env python3
"""
Helper script to guide users through getting AWS root account credentials.
"""

import webbrowser


def main():
    print("🔑 AWS Root Account Credentials Setup Guide")
    print("=" * 50)
    print()

    print("You need AWS root account credentials to fix the bootstrap user setup.")
    print("This is a one-time process. Here's how to get them:")
    print()

    # Step 1
    print("1️⃣  LOG INTO AWS CONSOLE AS ROOT USER")
    print("   • Go to: https://console.aws.amazon.com/")
    print("   • Use your AWS account EMAIL (not IAM username)")
    print("   • Use your AWS account PASSWORD")
    print()

    # Ask if they want to open the browser
    response = (
        input("🌐 Would you like me to open the AWS Console in your browser? (y/n): ")
        .lower()
        .strip()
    )
    if response in ["y", "yes"]:
        print("   Opening AWS Console...")
        webbrowser.open("https://console.aws.amazon.com/")
        print("   ✅ AWS Console opened in your browser")
        print()
        input("   Press ENTER when you've logged in as root user...")
        print()

    # Step 2
    print("2️⃣  NAVIGATE TO SECURITY CREDENTIALS")
    print("   • Click your account name (top right corner)")
    print("   • Select 'Security credentials' from the dropdown menu")
    print()
    input("   Press ENTER when you're on the Security Credentials page...")
    print()

    # Step 3
    print("3️⃣  CREATE ACCESS KEYS")
    print("   • Scroll down to the 'Access keys' section")
    print("   • Click 'Create access key' button")
    print("   • Select 'Command Line Interface (CLI)' as the use case")
    print("   • Check the confirmation checkbox")
    print("   • Click 'Create access key'")
    print()
    input("   Press ENTER when you see your new access keys...")
    print()

    # Step 4
    print("4️⃣  COPY YOUR ACCESS KEYS")
    print("   ⚠️  IMPORTANT: These keys are only shown ONCE!")
    print("   • Copy the 'Access key ID'")
    print("   • Copy the 'Secret access key'")
    print("   • Or download the .csv file")
    print()
    input("   Press ENTER when you've copied both keys...")
    print()

    # Step 5
    print("5️⃣  SET ENVIRONMENT VARIABLES")
    print("   Now paste your keys into these commands:")
    print()
    print('   export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID_HERE"')
    print('   export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY_HERE"')
    print('   export AWS_DEFAULT_REGION="us-east-1"')
    print()
    print("   Then verify you're running as root:")
    print("   aws sts get-caller-identity")
    print('   # Should show: "arn:aws:iam::ACCOUNT_ID:root"')
    print()

    # Step 6
    print("6️⃣  RUN THE BOOTSTRAP RESET")
    print("   Once you have root credentials set up:")
    print("   make bootstrap-destroy   # Remove broken setup")
    print("   make bootstrap-create    # Create proper setup")
    print()
    print("   Then update your .secrets file with the NEW bootstrap credentials")
    print("   and unset the root environment variables:")
    print("   unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY")
    print()

    print("🔒 SECURITY NOTE:")
    print("   After completing the bootstrap setup, DELETE the root access keys")
    print("   from the AWS Console. You only need them for this one-time fix.")
    print()

    print("✅ You're ready to fix your bootstrap setup!")
    print("   Run 'make bootstrap-reset-help' for the complete command sequence.")


if __name__ == "__main__":
    main()
