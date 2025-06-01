from core.mig_remote import execute_remote_gpu_cmd

host = "172.16.200.197"
username = "ubuntu"
key_path = "C:\\Users\\zorigoo\\.ssh\\test.pem"  # эсвэл pem байрлал
cmd = "nvidia-smi -L"  # эсвэл "nvidia-smi mig -lgi 0"

out, err = execute_remote_gpu_cmd(host, username, key_path, cmd)
print("=== GPU STATUS ===")
print(out)
print("=== ERRORS (if any) ===")
print(err)
