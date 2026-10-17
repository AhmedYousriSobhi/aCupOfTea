---
id: build-a-two-node-k3s-lab
sidebar_label: Build a Two-Node k3s Lab
summary: "Build a two-VM Kubernetes lab on your laptop with Vagrant, libvirt and k3s, and dodge the DNS and network potholes."
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc, devops, kubernates]
tags: [kubernetes, containers, hpc, devops]
relations:
  prerequisites: [kubernetes-in-five-nouns]
  related: [containers-101]
---

# Build a Two-Node Kubernetes Lab on Your Laptop (and Survive the DNS Pothole)

The fastest way to stop being afraid of a cluster is to own one you're allowed to break. This page builds exactly that: two tiny virtual machines, one Kubernetes control plane, one worker, and no cloud bill. It takes about twenty minutes, most of them spent watching images download and wondering whether the laptop fan is a smoke alarm.

Everything here was run on a real lab, and the potholes are real too. Read [Kubernetes in Five Nouns](/fields/devops/kubernetes/kubernetes-in-five-nouns.md) first if "node" and "pod" still feel like vocabulary words.

---

## The one-sentence version

**You'll create two Ubuntu VMs with Vagrant and libvirt, install k3s on one as the server and on the other as an agent, and end up with `kubectl get nodes` showing two `Ready` machines.**

k3s is a lightweight, certified Kubernetes distribution that ships as a single binary and bundles its container runtime and pod networking. It's a good fit for a lab precisely because it doesn't ask you to assemble twelve parts before you see your first node.

---

## What you'll end up with

| VM | Private IP | Role | Size used in the lab |
| --- | --- | --- | --- |
| `k8s-controller` | `192.168.57.10` | k3s server (API server, scheduler, controllers) | 1 GB RAM, 1 vCPU |
| `k8s-worker` | `192.168.57.11` | k3s agent (runs your pods) | 1 GB RAM, 1 vCPU |

A note on sizing. The k3s requirements page lists minimums per role, and the figures for a server are higher than for an agent, so check the current numbers there before building anything you care about. The lab runs a server on 1 GB and 1 vCPU, which works but is a squeeze: components like metrics-server can be slow to become healthy on a box this small. Treat it as a playground, not a template.

---

## Step 0: laptop prerequisites

On a Debian or Ubuntu laptop (adjust package names for your distro):

```bash
sudo apt install qemu-kvm libvirt-daemon-system libvirt-dev ruby-dev build-essential
sudo usermod -aG libvirt "$USER"            # log out and back in once
# install Vagrant from HashiCorp's repository, then:
vagrant plugin install vagrant-libvirt
virsh -c qemu:///system list --all          # must answer without an error
vagrant box add generic/ubuntu2204 --provider libvirt
free -m                                     # want roughly 3 GB available
```

If `virsh` complains, fix that before touching anything else. Every later error will blame Kubernetes when the real culprit is libvirt.

---

## Step 1: describe the VMs

```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu2204"
  config.vm.box_check_update = false
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.provider :libvirt do |lv|
    lv.memory = 1024
    lv.cpus = 1
  end
  { "controller" => "192.168.57.10", "worker" => "192.168.57.11" }.each do |name, ip|
    config.vm.define name do |m|
      m.vm.hostname = "k8s-#{name}"
      m.vm.network "private_network", ip: ip, libvirt__network_name: "k8s-lab",
        libvirt__dhcp_enabled: false, libvirt__forward_mode: "none"
    end
  end
end
```

Save it as `Vagrantfile` in an empty folder, then bring the machines up, with a `timeout` so a stuck boot can't hold your terminal hostage:

```bash
timeout 600 vagrant up controller --provider libvirt
timeout 600 vagrant up worker --provider libvirt
vagrant status
```

### Why every VM has two network cards

`eth0` is Vagrant's management network: it NATs to the internet so you can download things and so Vagrant can SSH in. `eth1` is the private network you just defined, with no DHCP and no forwarding, and it's where cluster traffic should travel. Forgetting this distinction is the classic way to build a cluster where pods on different nodes cannot talk to each other. We tell k3s which card to use in step 3.

---

## Step 2: prepare both VMs (and meet the DNS pothole)

Run this on **each** VM (`vagrant ssh controller`, then `vagrant ssh worker`).

### The pothole

On first boot, this lab's guests could not resolve `get.k3s.io`. The cause: the resolver tried IPv6 answers first, and there was no IPv6 route out. Name resolution "worked" in the sense that it returned an answer, and the answer led nowhere. The fix in the lab is unglamorous:

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1 net.ipv6.conf.default.disable_ipv6=1
sudo systemctl disable --now systemd-resolved
GW=$(ip -4 route show default | awk '{print $3; exit}')
sudo rm -f /etc/resolv.conf
printf 'nameserver %s\nnameserver 1.1.1.1\n' "$GW" | sudo tee /etc/resolv.conf
getent hosts get.k3s.io                       # must print an address
```

That's a blunt instrument for a lab with a flaky box image. On a real server you'd fix the IPv6 route or the resolver configuration properly instead of switching IPv6 off.

### Swap

```bash
sudo swapoff -a
sudo sed -i '/\sswap\s/d' /etc/fstab
```

A stock kubelet refuses to start with swap enabled unless you opt in, which is why every kubeadm guide tells you to disable it. k3s ships its own kubelet defaults, so check the k3s docs before assuming it applies, but turning swap off on cluster nodes is a habit that works on every path, so the lab does it.

### Can the nodes see each other?

```bash
ip -4 addr show eth1                          # 192.168.57.10 or .11
ping -c1 192.168.57.11                        # from the controller
```

---

## Step 3: the server

On the controller:

```bash
curl -4sfL https://get.k3s.io -o /tmp/k3s-install.sh
sudo INSTALL_K3S_EXEC="server --node-ip 192.168.57.10 --advertise-address 192.168.57.10 \
  --tls-san 192.168.57.10 --flannel-iface eth1 --disable traefik --disable servicelb \
  --write-kubeconfig-mode 644" \
  K3S_TOKEN="change-me-lab-token" sh /tmp/k3s-install.sh

sudo k3s kubectl get nodes                    # wait for Ready
sudo ln -sf /usr/local/bin/k3s /usr/local/bin/kubectl
cp /etc/rancher/k3s/k3s.yaml ~/kc-admin.yaml
chmod 600 ~/kc-admin.yaml
```

The install script and the `INSTALL_K3S_EXEC` and `K3S_TOKEN` variables are the documented way to configure k3s at install time. What each flag does:

| Flag | What it does |
| --- | --- |
| `--node-ip` | The IP this node advertises, pinned to `eth1` |
| `--advertise-address` | The address the API server tells cluster members to use |
| `--tls-san` | Adds that address to the API server's certificate, so connecting by it doesn't fail TLS verification |
| `--flannel-iface eth1` | Makes pod networking (flannel) use the private card |
| `--disable traefik`, `--disable servicelb` | Skips the bundled ingress and load balancer you don't need, saving memory on a tiny box |
| `--write-kubeconfig-mode 644` | Makes the generated kubeconfig readable by non-root users |

Two honesty notes. First, `644` means any local user can read the admin kubeconfig, which is acceptable on a throwaway VM and nowhere else. That's why the last two lines make a private copy with mode `600`. Second, the token is a join password. `change-me-lab-token` is a placeholder, and in any real cluster you'd generate something random and keep it out of scripts.

---

## Step 4: the worker joins

On the worker, wait for the server's API to answer, then join:

```bash
curl -4sfL https://get.k3s.io -o /tmp/k3s-install.sh
until curl -ksf https://192.168.57.10:6443/ping; do sleep 3; done   # bound this in real use
sudo K3S_URL="https://192.168.57.10:6443" K3S_TOKEN="change-me-lab-token" \
  INSTALL_K3S_EXEC="agent --node-ip 192.168.57.11 --flannel-iface eth1" sh /tmp/k3s-install.sh
```

Setting `K3S_URL` is what tells the install script to install an agent instead of a server. The `until` loop is the polite way to wait for the front desk to open; in anything beyond a lab, put a limit on it so a typo can't spin forever.

---

## Step 5: the checkpoint

Back on the controller:

```bash
export KUBECONFIG=~/kc-admin.yaml
kubectl get nodes -o wide                     # both Ready, in about a minute
kubectl -n kube-system get pods               # coredns, metrics-server, local-path-provisioner
```

Two `Ready` nodes means you have a cluster. If the worker never shows up, the usual suspects are the server's API not being reachable yet, or the wrong network card. The agent's logs say which:

```bash
vagrant ssh worker -c 'sudo journalctl -u k3s-agent -n 50'
```

---

## Tear it down

```bash
vagrant halt                      # keep the disks, stop the VMs
vagrant destroy -f                # delete the VMs entirely
virsh -c qemu:///system net-destroy k8s-lab 2>/dev/null   # stop the private network
```

Do this when you're finished. Two idle VMs quietly keep about 2 GB of RAM hostage.

---

## Pothole summary

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `getent hosts get.k3s.io` prints nothing | Resolver tries IPv6 first with no route | Step 2, or fix the resolver properly |
| Install script can't download | Same DNS problem | Same fix |
| Worker never joins | Server not up yet, or traffic on the wrong NIC | Wait, check `journalctl -u k3s-agent`, confirm `--flannel-iface` and `--node-ip` |
| Pods on different nodes can't talk | Flannel bound to `eth0` instead of `eth1` | Set `--flannel-iface eth1` on both nodes |
| `metrics-server` unhealthy | 1 GB boxes are slow to pass probes | Harmless here; CPU and memory columns stay empty until it answers |

---

## The one-paragraph takeaway

A Kubernetes lab is two VMs, two network cards each, and a handful of flags that say "use the private one." Fix DNS before blaming Kubernetes, point flannel and the node IPs at `eth1`, keep the admin kubeconfig private, and tear the thing down when you're done. Then you have a cluster you can break on purpose, which is the next page's business.

---

## References

- [K3s Requirements](https://docs.k3s.io/installation/requirements): per-role minimum CPU and RAM (check current figures)
- [K3s Configuration Options](https://docs.k3s.io/installation/configuration): the install script, `INSTALL_K3S_EXEC`, `K3S_URL`, `K3S_TOKEN`, `--write-kubeconfig-mode`, and the `/etc/rancher/k3s/config.yaml` alternative
- [K3s server configuration reference](https://docs.k3s.io/cli/server): `--node-ip`, `--advertise-address`, `--tls-san`, `--flannel-iface`, and the list of components `--disable` accepts

The Vagrant and libvirt setup, the DNS fix and the pothole table come from the author's own lab runs. The kubeadm alternative is deliberately not covered here because it hasn't been tested on this lab.