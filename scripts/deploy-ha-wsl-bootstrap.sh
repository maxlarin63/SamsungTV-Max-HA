#!/usr/bin/env bash
# Bootstrap: copy ha_deploy key from Windows ~/.ssh into WSL ~/.ssh with correct permissions.
# OpenSSH rejects keys under /mnt/c because NTFS gives them mode 0777.

WIN_HOME=$(wslpath "$(cmd.exe /C "echo %USERPROFILE%" 2>/dev/null | tr -d '\r')")
WIN_KEY="$WIN_HOME/.ssh/ha_deploy"
WSL_KEY="$HOME/.ssh/ha_deploy"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [[ -f "$WIN_KEY" && ! -f "$WSL_KEY" ]]; then
    cp "$WIN_KEY" "$WSL_KEY"
    chmod 600 "$WSL_KEY"
    echo "✓ ha_deploy key copied to WSL ~/.ssh"
elif [[ -f "$WSL_KEY" ]]; then
    chmod 600 "$WSL_KEY"
fi
