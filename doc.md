

## Since you have **Docker Desktop** on your laptop and you’re using **Visual Studio Code (VSCode)**, you can easily use a **Linux shell (bash)** or **WSL** inside VSCode.

---

## Step-by-step: Using Linux Shell (bash/WSL) in VSCode

---

Powershell command: 
### Option 1: WSL (Windows Subsystem for Linux) Integration

#### Step 1: Check if WSL is installed

Run the following in **PowerShell or CMD**:

```powershell
wsl --list --verbose
```

If it shows something like:

```
NAME      STATE           VERSION
Ubuntu    Running         2
```

## Ubuntu WSL terminal in VScode: 

```bash
wsl -d Ubuntu
```

ubuntu linux shell: 
sudo apt-get update && sudo apt-get install -y jq

Docker Desktop → WSL Integration Enable করো
Windows এ Docker Desktop খুলো

⚙️ Settings → Resources → WSL Integration

নিচে দেখাবে:
✅ Enable integration with my default WSL distro
✅ Ubuntu
🔁 Enable বাটন অন করো

```bash
docker version
docker compose version
sudo docker compose up --build -d

```





auto mq= apache kafka er alternative