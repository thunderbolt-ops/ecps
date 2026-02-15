#!/usr/bin/env python3
"""
ecpsctl - ECPS Control Plane CLI

A self-service tool for application teams to onboard services,
manage deployments, and interact with the ECPS platform.

Usage:
  ecpsctl init                  Initialize ECPS configuration
  ecpsctl service create        Scaffold a new microservice
  ecpsctl service deploy        Deploy a service to an environment
  ecpsctl service list          List all running services
  ecpsctl service status        Get service health and metrics
  ecpsctl service logs          Stream service logs
  ecpsctl service scale         Adjust replica count
  ecpsctl config set            Set platform configuration
  ecpsctl config get            Get current configuration
  ecpsctl cluster info          Show cluster information
  ecpsctl help                  Show detailed help

"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import yaml

__version__ = "0.2.0"

class ECPSCtl:
    def __init__(self):
        self.config_dir = Path.home() / ".ecps"
        self.config_file = self.config_dir / "config.yaml"
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self.setup_default_config()
    
    def setup_default_config(self):
        """Create default configuration"""
        config = {
            "team": os.getenv("ECPS_TEAM", "team-alpha"),
            "environment": os.getenv("ECPS_ENV", "dev"),
            "namespace": os.getenv("ECPS_NAMESPACE", "team-alpha"),
            "cluster": os.getenv("ECPS_CLUSTER", "ecps-dev"),
            "registry": "localhost:5000",
            "version": __version__,
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config, f)
        print(f"✅ Created default config: {self.config_file}")
    
    def load_config(self):
        """Load configuration from file"""
        with open(self.config_file, "r") as f:
            return yaml.safe_load(f)
    
    # ===== Service Management =====
    
    def service_create(self, args):
        """
        Scaffold a new microservice from template
        
        Usage:
          ecpsctl service create --name billing-api --language python
        """
        name = args.name or input("Service name: ")
        language = args.language or input("Language (python/go/node): ")
        
        # Validate
        if not name or not language:
            print("❌ Name and language are required")
            sys.exit(1)
        
        # Template locations
        templates = {
            "python": "templates/service-python",
            "go": "templates/service-go",
            "node": "templates/service-node",
        }
        
        if language not in templates:
            print(f"❌ Unknown language: {language}")
            print(f"   Supported: {', '.join(templates.keys())}")
            sys.exit(1)
        
        # Create service directory
        service_dir = Path(f"apps/team-alpha/{name}")
        service_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Creating {language} service '{name}'")
        print(f"   Location: {service_dir}")
        
        # TODO: Copy template files
        print(f"\n📝 Next steps:")
        print(f"   1. cd {service_dir}")
        print(f"   2. Edit src/main.py (or equivalent)")
        print(f"   3. Edit k8s/deployment.yaml")
        print(f"   4. Run: ecpsctl service deploy --name {name}")
    
    def service_deploy(self, args):
        """
        Deploy a service to an environment
        
        Usage:
          ecpsctl service deploy --name billing-api --env dev
        """
        config = self.load_config()
        name = args.name or config.get("service")
        env = args.env or config.get("environment")
        
        if not name:
            print("❌ Service name is required (--name)")
            sys.exit(1)
        
        print(f"🚀 Deploying {name} to {env}...")
        
        # Check if service exists
        service_dir = Path(f"apps/team-alpha/{name}")
        if not service_dir.exists():
            print(f"❌ Service not found: {service_dir}")
            sys.exit(1)
        
        # Build Docker image
        print(f"📦 Building Docker image...")
        docker_cmd = f"docker build -t {name}:latest {service_dir}"
        try:
            subprocess.run(docker_cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            print(f"❌ Docker build failed")
            sys.exit(1)
        
        # Load image into kind
        cluster = f"ecps-{env}"
        print(f"📤 Loading image into {cluster}...")
        kind_cmd = f"kind load docker-image {name}:latest --name {cluster}"
        subprocess.run(kind_cmd, shell=True, check=False)
        
        # Apply Kubernetes manifests
        print(f"⚙️  Applying Kubernetes manifests...")
        ns = f"team-alpha"  # TODO: Make configurable
        manifest_dir = service_dir / "k8s"
        
        if manifest_dir.exists():
            for manifest in manifest_dir.glob("*.yaml"):
                kubectl_cmd = f"kubectl apply -f {manifest} -n {ns}"
                subprocess.run(kubectl_cmd, shell=True, check=False)
        
        print(f"✅ Deployment initiated!")
        print(f"   Check status: ecpsctl service status --name {name}")
    
    def service_list(self, args):
        """
        List all services in current team and environment
        
        Usage:
          ecpsctl service list
          ecpsctl service list --all-environments
        """
        config = self.load_config()
        namespace = config.get("namespace", "team-alpha")
        
        print(f"📋 Services in {namespace}:")
        print()
        
        # Run kubectl to get services
        cmd = f"kubectl get svc -n {namespace} -o json"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            services = json.loads(result.stdout)
            
            if not services.get("items"):
                print("   (no services found)")
                return
            
            # Print table
            print(f"{'NAME':<20} {'TYPE':<12} {'CLUSTER-IP':<15} {'EXTERNAL-IP':<15} {'PORT(S)':<20}")
            print("─" * 82)
            
            for svc in services.get("items", []):
                meta = svc.get("metadata", {})
                spec = svc.get("spec", {})
                
                name = meta.get("name")
                svc_type = spec.get("type")
                cluster_ip = spec.get("clusterIP")
                external_ip = spec.get("externalIP") or "<none>"
                
                ports = spec.get("ports", [])
                port_str = ", ".join([
                    f"{p.get('port')}/{p.get('protocol', 'TCP')}"
                    for p in ports
                ])
                
                print(f"{name:<20} {svc_type:<12} {cluster_ip:<15} {external_ip:<15} {port_str:<20}")
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to list services: {e}")
            sys.exit(1)
    
    def service_status(self, args):
        """
        Get status and metrics for a service
        
        Usage:
          ecpsctl service status --name billing-api
        """
        config = self.load_config()
        name = args.name or config.get("service")
        namespace = config.get("namespace", "team-alpha")
        
        if not name:
            print("❌ Service name is required (--name)")
            sys.exit(1)
        
        print(f"📊 Status: {name}")
        print()
        
        # Get deployment status
        cmd = f"kubectl get deployment {name} -n {namespace} -o json"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            deploy = json.loads(result.stdout)
            
            spec = deploy.get("spec", {})
            status = deploy.get("status", {})
            
            print(f"Replicas: {status.get('readyReplicas')}/{spec.get('replicas')}")
            print(f"Updated:  {status.get('updatedReplicas')}")
            print(f"Available: {status.get('availableReplicas')}")
            
            # Get pods
            print(f"\n🔷 Pods:")
            pods_cmd = f"kubectl get pods -n {namespace} -l app={name} -o wide"
            subprocess.run(pods_cmd, shell=True)
            
            # Get recent logs
            print(f"\n📝 Recent logs:")
            logs_cmd = f"kubectl logs -n {namespace} -l app={name} --tail=5"
            subprocess.run(logs_cmd, shell=True)
        
        except subprocess.CalledProcessError:
            print(f"❌ Service not found: {name}")
            sys.exit(1)
    
    def service_logs(self, args):
        """
        Stream live logs from a service
        
        Usage:
          ecpsctl service logs --name billing-api
          ecpsctl service logs --name billing-api --lines 100
        """
        config = self.load_config()
        name = args.name or config.get("service")
        namespace = config.get("namespace", "team-alpha")
        lines = args.lines or "50"
        
        if not name:
            print("❌ Service name is required (--name)")
            sys.exit(1)
        
        cmd = f"kubectl logs -n {namespace} -l app={name} --tail={lines} -f"
        try:
            subprocess.run(cmd, shell=True)
        except KeyboardInterrupt:
            print("\n⏹  Stopped log streaming")
    
    def service_scale(self, args):
        """
        Scale a service to a different replica count
        
        Usage:
          ecpsctl service scale --name billing-api --replicas 3
        """
        config = self.load_config()
        name = args.name or config.get("service")
        namespace = config.get("namespace", "team-alpha")
        replicas = args.replicas
        
        if not name or not replicas:
            print("❌ Service name and replica count are required")
            sys.exit(1)
        
        print(f"📈 Scaling {name} to {replicas} replicas...")
        
        cmd = f"kubectl scale deployment {name} --replicas={replicas} -n {namespace}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"✅ Scaled to {replicas} replicas")
            print(f"   Watch: kubectl rollout status deployment/{name} -n {namespace}")
        except subprocess.CalledProcessError:
            print(f"❌ Scale failed")
            sys.exit(1)
    
    # ===== Config Management =====
    
    def config_set(self, args):
        """
        Set a configuration value
        
        Usage:
          ecpsctl config set team team-beta
          ecpsctl config set environment stage
        """
        key = args.key
        value = args.value
        
        if not key or not value:
            print("❌ Key and value are required")
            sys.exit(1)
        
        config = self.load_config()
        config[key] = value
        
        with open(self.config_file, "w") as f:
            yaml.dump(config, f)
        
        print(f"✅ Set {key} = {value}")
    
    def config_get(self, args):
        """
        Get current configuration
        
        Usage:
          ecpsctl config get
          ecpsctl config get team
        """
        config = self.load_config()
        
        key = args.key
        if key:
            value = config.get(key)
            if value:
                print(value)
            else:
                print(f"❌ Key not found: {key}")
                sys.exit(1)
        else:
            print(f"📋 Current configuration:")
            print()
            for k, v in config.items():
                print(f"  {k:<20} = {v}")
    
    # ===== Cluster Info =====
    
    def cluster_info(self, args):
        """
        Show cluster information
        
        Usage:
          ecpsctl cluster info
        """
        print(f"ℹ️  ECPS Cluster Information")
        print()
        
        # Get nodes
        print(f"🖥️  Nodes:")
        subprocess.run("kubectl get nodes -o wide", shell=True)
        print()
        
        # Get namespaces
        print(f"📦 Namespaces:")
        subprocess.run("kubectl get namespaces", shell=True)
        print()
        
        # Get core services
        print(f"⚙️  Platform Services (platform-system):")
        subprocess.run("kubectl get svc -n platform-system", shell=True)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ECPS Control Plane CLI - Self-Service Platform Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ecpsctl service create --name hello-api --language python
  ecpsctl service deploy --name hello-api --env dev
  ecpsctl service list
  ecpsctl service status --name hello-api
  ecpsctl service scale --name hello-api --replicas 3
  ecpsctl config set environment stage
  ecpsctl cluster info
        """
    )
    
    parser.add_argument("--version", action="version", version=f"ecpsctl {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # service subcommand
    service_parser = subparsers.add_parser("service", help="Manage services")
    service_subparsers = service_parser.add_subparsers(dest="subcommand", help="Service operation")
    
    # service create
    create_parser = service_subparsers.add_parser("create", help="Create a new service")
    create_parser.add_argument("--name", help="Service name")
    create_parser.add_argument("--language", help="Language (python/go/node)")
    create_parser.set_defaults(func=lambda args: ECPSCtl().service_create(args))
    
    # service deploy
    deploy_parser = service_subparsers.add_parser("deploy", help="Deploy a service")
    deploy_parser.add_argument("--name", help="Service name")
    deploy_parser.add_argument("--env", help="Environment (dev/stage/prod)")
    deploy_parser.set_defaults(func=lambda args: ECPSCtl().service_deploy(args))
    
    # service list
    list_parser = service_subparsers.add_parser("list", help="List services")
    list_parser.add_argument("--all-environments", action="store_true", help="List all environments")
    list_parser.set_defaults(func=lambda args: ECPSCtl().service_list(args))
    
    # service status
    status_parser = service_subparsers.add_parser("status", help="Get service status")
    status_parser.add_argument("--name", required=True, help="Service name")
    status_parser.set_defaults(func=lambda args: ECPSCtl().service_status(args))
    
    # service logs
    logs_parser = service_subparsers.add_parser("logs", help="Stream service logs")
    logs_parser.add_argument("--name", required=True, help="Service name")
    logs_parser.add_argument("--lines", help="Number of previous log lines")
    logs_parser.set_defaults(func=lambda args: ECPSCtl().service_logs(args))
    
    # service scale
    scale_parser = service_subparsers.add_parser("scale", help="Scale a service")
    scale_parser.add_argument("--name", required=True, help="Service name")
    scale_parser.add_argument("--replicas", type=int, required=True, help="Number of replicas")
    scale_parser.set_defaults(func=lambda args: ECPSCtl().service_scale(args))
    
    # config subcommand
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_subcmd", help="Config operation")
    
    # config set
    set_parser = config_subparsers.add_parser("set", help="Set a config value")
    set_parser.add_argument("key", help="Config key")
    set_parser.add_argument("value", help="Config value")
    set_parser.set_defaults(func=lambda args: ECPSCtl().config_set(args))
    
    # config get
    get_parser = config_subparsers.add_parser("get", help="Get config values")
    get_parser.add_argument("key", nargs="?", help="Config key (optional)")
    get_parser.set_defaults(func=lambda args: ECPSCtl().config_get(args))
    
    # cluster subcommand
    cluster_parser = subparsers.add_parser("cluster", help="Cluster information")
    cluster_subparsers = cluster_parser.add_subparsers(dest="cluster_subcmd", help="Cluster operation")
    
    # cluster info
    info_parser = cluster_subparsers.add_parser("info", help="Show cluster info")
    info_parser.set_defaults(func=lambda args: ECPSCtl().cluster_info(args))
    
    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
