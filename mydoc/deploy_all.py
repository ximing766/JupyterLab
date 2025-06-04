#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多项目自动化部署脚本
用于管理mydoc下的多个GitHub项目的统一部署

作者: ximing766
创建时间: 2024
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime
import argparse

class ProjectManager:
    """项目管理器，用于统一管理多个GitHub项目"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.config_file = self.base_dir / "deploy_config.json"
        self.projects = self.load_config()
        
    def load_config(self) -> Dict:
        """加载项目配置"""
        default_config = {
            "projects": {
                "github.io": {
                    "path": "github.io",
                    "branch": "master",
                    "description": "主页项目",
                    "build_command": None,
                    "deploy_to_pages": True
                },
                "UwbKnowledgePoints": {
                    "path": "UwbKnowledgePoints",
                    "branch": "master",
                    "description": "UWB技术文档",
                    "build_command": "mkdocs build",
                    "deploy_to_pages": True
                },
                "UWB_Application_Plan": {
                    "path": "UWB_Application_Plan",
                    "branch": "master",
                    "description": "UWB应用计划文档",
                    "build_command": "mkdocs build",
                    "deploy_to_pages": True
                },
                "my-project-doc": {
                    "path": "my-project-doc",
                    "branch": "main",
                    "description": "项目文档模板",
                    "build_command": "mkdocs build",
                    "deploy_to_pages": True
                }
            },
            "global_settings": {
                "default_commit_message": "docs: 更新文档内容",
                "auto_add_all": True,
                "push_after_commit": True,
                "deploy_to_gh_pages": True
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  配置文件读取失败，使用默认配置: {e}")
                return default_config
        else:
            # 创建默认配置文件
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
    
    def run_command(self, command: str, cwd: Path) -> tuple:
        """在指定目录执行命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors = 'ignore'
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_git_status(self, project_path: Path) -> Dict:
        """检查Git状态"""
        if not (project_path / ".git").exists():
            return {"is_git_repo": False, "has_changes": False, "status": "Not a git repository"}
        
        success, stdout, stderr = self.run_command("git status --porcelain", project_path)
        if not success:
            return {"is_git_repo": True, "has_changes": False, "status": f"Error: {stderr}"}
        
        has_changes = bool(stdout.strip())
        return {
            "is_git_repo": True,
            "has_changes": has_changes,
            "status": "Clean" if not has_changes else "Has changes",
            "changes": stdout.strip().split('\n') if has_changes else []
        }
    
    def commit_and_push(self, project_name: str, commit_message: str = None) -> bool:
        """提交并推送指定项目"""
        project_config = self.projects["projects"].get(project_name)
        if not project_config:
            print(f"❌ 项目 {project_name} 不存在于配置中")
            return False
        
        project_path = self.base_dir / project_config["path"]
        if not project_path.exists():
            print(f"❌ 项目路径不存在: {project_path}")
            return False
        
        print(f"\n🔄 处理项目: {project_name} ({project_config['description']})")
        print(f"📁 路径: {project_path}")
        
        # 检查Git状态
        git_status = self.check_git_status(project_path)
        if not git_status["is_git_repo"]:
            print(f"⚠️  {project_name} 不是Git仓库，跳过")
            return False
        
        if not git_status["has_changes"]:
            print(f"✅ {project_name} 没有变更，跳过")
            return True
        
        print(f"📝 发现变更:")
        for change in git_status["changes"]:
            print(f"   {change}")
        
        # 添加所有变更
        if self.projects["global_settings"]["auto_add_all"]:
            success, stdout, stderr = self.run_command("git add .", project_path)
            if not success:
                print(f"❌ 添加文件失败: {stderr}")
                return False
            print("✅ 已添加所有变更")
        
        # 提交
        if not commit_message:
            commit_message = self.projects["global_settings"]["default_commit_message"]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_commit_message = f"{commit_message} - {timestamp}"
        
        success, stdout, stderr = self.run_command(
            f'git commit -m "{full_commit_message}"', 
            project_path
        )
        if not success:
            print(f"❌ 提交失败: {stderr}")
            return False
        print(f"✅ 提交成功: {full_commit_message}")
        
        # 推送
        if self.projects["global_settings"]["push_after_commit"]:
            branch = project_config.get("branch", "master")
            success, stdout, stderr = self.run_command(
                f"git push origin {branch}", 
                project_path
            )
            if not success:
                print(f"❌ 推送失败: {stderr}")
                return False
            print(f"✅ 推送成功到 {branch} 分支")
        
        # 部署到GitHub Pages（如果需要）
        if (project_config.get("deploy_to_pages", False) and 
            project_config.get("build_command") and
            self.projects["global_settings"]["deploy_to_gh_pages"]):
            
            print(f"🚀 开始部署到GitHub Pages...")
            
            # 构建文档
            success, stdout, stderr = self.run_command(
                project_config["build_command"], 
                project_path
            )
            if not success:
                print(f"⚠️  构建失败: {stderr}")
            else:
                print("✅ 构建成功")
                
                # 部署到gh-pages
                success, stdout, stderr = self.run_command(
                    "mkdocs gh-deploy --force", 
                    project_path
                )
                if not success:
                    print(f"⚠️  GitHub Pages部署失败: {stderr}")
                else:
                    print("🎉 GitHub Pages部署成功")
        
        return True
    
    def deploy_all(self, commit_message: str = None, exclude: List[str] = None) -> Dict:
        """部署所有项目"""
        exclude = exclude or []
        results = {}
        
        print("🚀 开始批量部署所有项目...")
        print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        for project_name in self.projects["projects"]:
            if project_name in exclude:
                print(f"⏭️  跳过项目: {project_name}")
                results[project_name] = "skipped"
                continue
            
            try:
                success = self.commit_and_push(project_name, commit_message)
                results[project_name] = "success" if success else "failed"
            except Exception as e:
                print(f"❌ 项目 {project_name} 处理异常: {e}")
                results[project_name] = "error"
        
        # 输出总结
        print("\n" + "=" * 60)
        print("📊 部署总结:")
        success_count = sum(1 for status in results.values() if status == "success")
        total_count = len([p for p in self.projects["projects"] if p not in exclude])
        
        print(f"✅ 成功: {success_count}/{total_count}")
        
        for project_name, status in results.items():
            status_emoji = {
                "success": "✅",
                "failed": "❌",
                "error": "💥",
                "skipped": "⏭️"
            }
            print(f"   {status_emoji.get(status, '❓')} {project_name}: {status}")
        
        return results
    
    def status_all(self):
        """查看所有项目状态"""
        print("📋 项目状态概览:")
        print("=" * 80)
        
        for project_name, project_config in self.projects["projects"].items():
            project_path = self.base_dir / project_config["path"]
            print(f"\n📁 {project_name} ({project_config['description']})")
            print(f"   路径: {project_path}")
            
            if not project_path.exists():
                print("   ❌ 路径不存在")
                continue
            
            git_status = self.check_git_status(project_path)
            if not git_status["is_git_repo"]:
                print("   ⚠️  不是Git仓库")
                continue
            
            print(f"   📊 状态: {git_status['status']}")
            if git_status["has_changes"]:
                print("   📝 变更文件:")
                for change in git_status["changes"][:5]:  # 只显示前5个
                    print(f"      {change}")
                if len(git_status["changes"]) > 5:
                    print(f"      ... 还有 {len(git_status['changes']) - 5} 个文件")
    
    def init_project(self, project_name: str, project_path: str, description: str = ""):
        """初始化新项目配置"""
        if project_name in self.projects["projects"]:
            print(f"⚠️  项目 {project_name} 已存在")
            return False
        
        self.projects["projects"][project_name] = {
            "path": project_path,
            "branch": "master",
            "description": description or f"{project_name} 项目",
            "build_command": None,
            "deploy_to_pages": False
        }
        
        self.save_config(self.projects)
        print(f"✅ 项目 {project_name} 已添加到配置")
        return True

def main():
    parser = argparse.ArgumentParser(description="多项目自动化部署工具")
    parser.add_argument("action", choices=["deploy", "status", "init", "config"], 
                       help="执行的操作")
    parser.add_argument("-m", "--message", help="提交信息")
    parser.add_argument("-e", "--exclude", nargs="*", help="排除的项目")
    parser.add_argument("-p", "--project", help="指定单个项目")
    parser.add_argument("--name", help="项目名称（用于init）")
    parser.add_argument("--path", help="项目路径（用于init）")
    parser.add_argument("--desc", help="项目描述（用于init）")
    
    args = parser.parse_args()
    
    manager = ProjectManager()
    
    if args.action == "deploy":
        if args.project:
            # 部署单个项目
            success = manager.commit_and_push(args.project, args.message)
            sys.exit(0 if success else 1)
        else:
            # 部署所有项目
            results = manager.deploy_all(args.message, args.exclude)
            failed_count = sum(1 for status in results.values() 
                             if status in ["failed", "error"])
            sys.exit(0 if failed_count == 0 else 1)
    
    elif args.action == "status":
        manager.status_all()
    
    elif args.action == "init":
        if not args.name or not args.path:
            print("❌ 初始化项目需要 --name 和 --path 参数")
            sys.exit(1)
        manager.init_project(args.name, args.path, args.desc or "")
    
    elif args.action == "config":
        print(f"📄 配置文件位置: {manager.config_file}")
        print("\n当前配置:")
        print(json.dumps(manager.projects, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()