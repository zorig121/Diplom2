# app/core/mig_remote.py

import paramiko

def execute_remote_gpu_cmd(host: str, username: str, key_path: str, command: str) -> tuple[str, str]:
    """
    Remote SSH execution for GPU commands
    :return: (stdout, stderr)
    """
    key = paramiko.RSAKey.from_private_key_file(key_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, pkey=key)

    stdin, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    ssh.close()
    return out, err
