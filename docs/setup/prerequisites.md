# Install

Install three tools, then download the project. You will work in VS Code for everything. Windows, macOS and Ubuntu (including WSL) are supported.

## 1. VS Code

[Download VS Code](https://code.visualstudio.com/) and install it. Open it, and accept the recommended extensions (Python and Docker) when it offers them.

## 2. pixi

pixi installs the project's software for you. In VS Code open a terminal (**Terminal > New Terminal**) and run the command for your system, then close and reopen VS Code.

=== "macOS / Linux"
    ```bash
    curl -fsSL https://pixi.sh/install.sh | bash
    ```
=== "Windows (PowerShell)"
    ```powershell
    iwr -useb https://pixi.sh/install.ps1 | iex
    ```

## 3. Docker

Docker runs your practice patient server.

=== "macOS"
    1. Download [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/). Pick **Apple silicon** or **Intel** (Apple menu > About This Mac).
    2. Drag **Docker** into **Applications** and open it.
    3. Accept the agreement. You do not need to sign in.
=== "Windows"
    1. Download [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) and run the installer with the default options (WSL 2). Restart if it asks.
    2. Start Docker Desktop from the Start menu. It does not start by itself after installing.
    3. Accept the agreement. You do not need to sign in.
=== "Ubuntu"
    Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/), then run this and log out and back in:

    ```bash
    sudo usermod -aG docker $USER
    ```

Needs: Windows 10 (22H2) or 11 with 8 GB of RAM and virtualization turned on in the BIOS (usually already on); macOS with 4 GB of RAM, the current or one of the two previous versions.

Wait until Docker Desktop says it is running, then check in the VS Code terminal:

```bash
docker ps
```

If it says it cannot connect, Docker is not running yet.

!!! note "Docker Desktop licensing"
    Free for education and personal use. Larger organizations, such as many hospitals, need a paid subscription for work use: ask your IT department if this is a work computer.

## 4. Get the project

On [github.com/tonyreina/ehr_sandbox](https://github.com/tonyreina/ehr_sandbox) click **Code > Download ZIP** and unzip it (or `git clone https://github.com/tonyreina/ehr_sandbox.git`). In VS Code choose **File > Open Folder** and open it. Then run:

```bash
pixi install
```

The first run takes a few minutes. Next: [Connect Codex](codex.md).
