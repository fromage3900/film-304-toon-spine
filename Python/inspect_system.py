import psutil

print("=== MEMORY SUMMARY ===")
vm = psutil.virtual_memory()
sm = psutil.swap_memory()
print(f"RAM: Total={vm.total/(1024**3):.1f}GB, Available={vm.available/(1024**3):.1f}GB, Used={vm.used/(1024**3):.1f}GB ({vm.percent}%)")
print(f"SWAP/PAGEFILE: Total={sm.total/(1024**3):.1f}GB, Free={sm.free/(1024**3):.1f}GB, Used={sm.used/(1024**3):.1f}GB ({sm.percent}%)")

print("\n=== TOP 20 PROCESSES BY COMMIT / RSS ===")
procs = []
for p in psutil.process_iter(['pid', 'name', 'memory_info']):
    try:
        mem = p.info['memory_info']
        if mem:
            rss = mem.rss / (1024 * 1024)
            vms = getattr(mem, 'vms', 0) / (1024 * 1024)
            procs.append((p.info['pid'], p.info['name'], rss, vms))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

procs.sort(key=lambda x: x[3], reverse=True)
for pid, name, rss, vms in procs[:20]:
    print(f"{pid:6d}  {name:30s}  RSS: {rss:7.1f} MB  Commit/VMS: {vms:8.1f} MB")
