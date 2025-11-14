#!/bin/bash
set -euo pipefail

###############################################################################
# rclone Setup Guide for Google Drive
#
# This script will guide you through installing and configuring rclone
# for Google Drive backups
###############################################################################

echo "========================================="
echo "rclone Setup for Google Drive"
echo "========================================="
echo ""

# Check if rclone is already installed
if command -v rclone &> /dev/null; then
    echo "✓ rclone is already installed: $(rclone version | head -n1)"
    echo ""
else
    echo "Installing rclone..."
    curl https://rclone.org/install.sh | sudo bash
    echo ""
fi

echo "========================================="
echo "Next Steps: Configure Google Drive"
echo "========================================="
echo ""
echo "Run the following command to configure rclone:"
echo ""
echo "  rclone config"
echo ""
echo "Follow these steps:"
echo "  1. Type 'n' for New remote"
echo "  2. Name: gdrive"
echo "  3. Storage: 18 (Google Drive)"
echo "  4. client_id: [press Enter]"
echo "  5. client_secret: [press Enter]"
echo "  6. scope: 1 (Full access)"
echo "  7. service_account_file: [press Enter]"
echo "  8. Edit advanced config: n"
echo "  9. Use web browser to automatically authenticate: y"
echo "  10. Follow browser authentication"
echo "  11. Configure as team drive: n"
echo "  12. Confirm: y"
echo "  13. Quit: q"
echo ""
echo "After configuration, test with:"
echo "  rclone lsd gdrive:"
echo ""
echo "Then create backup folder:"
echo "  rclone mkdir gdrive:n8n-backups"
echo ""
echo "========================================="
