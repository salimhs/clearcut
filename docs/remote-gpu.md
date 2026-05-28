# Remote GPU Processing

ClearCut can offload video processing to a remote machine with a powerful GPU. This is useful when:

- Your local machine doesn't have a dedicated GPU
- The remote machine has faster NVENC/AMF encoding
- You have a headless server with GPU that you want to utilize

## How It Works

The `clearcut remote` command:

1. Copies your input video to the remote machine via `rsync` over SSH
2. Runs the full processing pipeline on the remote machine (with CUDA/NVENC)
3. Copies the output back to your local machine
4. Cleans up all temporary files on the remote machine

!!! note
    No files are left on the remote machine after processing completes.

## Prerequisites

### 1. Tailscale (Recommended)

Both machines need to be on the same [Tailscale](https://tailscale.com) network for fast, secure transfers.

```bash
# On both machines
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### 2. SSH Key Authentication

Set up passwordless SSH access from your local machine to the remote machine:

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519

# Copy to remote machine
ssh-copy-id user@remote-tailscale-ip

# Verify it works
ssh user@remote-tailscale-ip "echo 'Connected!'"
```

### 3. ClearCut Installed on Remote

The remote machine needs ClearCut installed:

```bash
ssh user@remote-ip "pip install 'clearcut[all]'"
```

## Usage

### Basic Remote Processing

```bash
clearcut remote \
  --input ~/videos/take1.mp4 \
  --output ~/output/final.mp4 \
  --host 100.97.187.60
```

### With Captions (Requires GPU)

```bash
clearcut remote \
  --input ~/videos/take1.mp4 \
  --output ~/output/final.mp4 \
  --host 100.97.187.60 \
  --captions
```

### With Template

```bash
clearcut remote \
  --input ~/videos/take1.mp4 \
  --output ~/output/tiktok_clip.mp4 \
  --host 100.97.187.60 \
  --captions \
  --template tiktok
```

### Full Options

```bash
clearcut remote \
  --input take1.mp4 \
  --output final.mp4 \
  --host 100.97.187.60 \
  --user myuser \
  --captions \
  --template tiktok \
  --format 9:16 \
  --no-silence
```

## Example Workflow

```bash
# 1. On local machine: check if you need remote GPU
clearcut info
# → Shows no GPU acceleration available

# 2. Process on remote GPU machine
clearcut remote \
  --input raw_interview.mp4 \
  --output polished_interview.mp4 \
  --host 100.97.187.60 \
  --captions \
  --burn \
  --template clean

# 3. File is transferred back to your local machine
#    polished_interview.mp4 is ready to use
```

## Default Host

The default remote host is `100.97.187.60`. You can change this in the command or set up an alias.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Ensure Tailscale is running on both machines and you can ping the remote IP |
| `Permission denied` | Set up SSH key authentication with `ssh-copy-id` |
| `rsync not found` | Install rsync on both machines: `sudo apt install rsync` |
| `clearcut: command not found` on remote | Install ClearCut on the remote machine |
| Slow transfers | Both machines should be on the same Tailscale network for direct peer-to-peer connections |
