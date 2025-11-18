# Auto Git Backup

Automatically backup directories using Git with systemd timers.

## Setup Instructions

### 1. Make the Script Executable

```bash
chmod +x /path/to/auto_git_backup_master.py
```

### 2. Initialize Git Repositories

#### Initialize Each Folder You Want to Backup

```bash
cd /path/to/folder1
git init
# Set up .gitignore etc. as you like
```

#### Initialize the Master Folder

```bash
cd /path/to/master
git init
```

### 3. Configure Systemd Service

Create the service file at `~/.config/systemd/user/auto-git-backup.service`:

```ini
[Unit]
Description=Auto Git Backup

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/you/auto_git_backup.py
```

### 4. Configure Systemd Timer

Create the timer file at `~/.config/systemd/user/auto-git-backup.timer`:

```ini
[Unit]
Description=Run Auto Git Backup every 10 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=10min

[Install]
WantedBy=default.target
```

### 5. Enable and Start the Timer

```bash
systemctl --user enable auto-git-backup.timer
systemctl --user start auto-git-backup.timer
```
