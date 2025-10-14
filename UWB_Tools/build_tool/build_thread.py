#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
                        UWB Build Tool - Build Thread Module
==============================================================================

Description:
    Multi-threaded build execution module for UWB applications. Handles both
    MCUXpresso IDE (CDT) builds and make-based compilation in separate threads
    to prevent GUI blocking during build operations.

Author:         Cardshare@QLL
Created:        2025
Version:        1.0.0

==============================================================================
"""

import os
import subprocess
import json
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

class BuildThread(QThread):
    build_started = pyqtSignal()
    build_progress = pyqtSignal(str)
    build_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = ""
        self.config_mode = "Debug"
    
    def setup_build(self, project_path: str, config_mode: str):
        self.project_path = project_path
        self.config_mode = config_mode
        self.is_rebuild = False
        
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.ide_path = config.get("mcuxpresso_ide_path", "mcuxpressoidec.exe")
            self.workspace_path = config.get("mcuxpresso_workspace_path", "workspace")
        except Exception as e:
            self.ide_path = "mcuxpressoidec.exe"
            self.workspace_path = "workspace"
    
    def setup_rebuild(self, project_path: str, config_mode: str):
        self.setup_build(project_path, config_mode)
        self.is_rebuild = True
    
    def setup_make(self, project_path: str, config_mode: str, scheme_name: str = None):
        self.project_path = project_path
        self.config_mode = config_mode
        self.scheme_name = scheme_name
        self.is_make = True
    
    def should_show_line(self, line: str) -> bool:
        line_lower = line.lower().strip()
        
        if not line_lower:
            return False
        
        compiler_linker_patterns = [
            'arm-none-eabi-gcc',
            'arm-none-eabi-g++',
            'arm-none-eabi-ld',
            '-nostdlib',
            '-xlinker',
            '-mcpu=',
            '-mthumb',
            '.o '
        ]
        
        if any(pattern in line_lower for pattern in compiler_linker_patterns):
            return False
        if any(keyword in line_lower for keyword in ['error', 'failed', 'failure']):
            return True
        return True
    
    def run(self):
        try:
            self.build_started.emit()
            if hasattr(self, 'is_make') and self.is_make:
                self._run_make_build()
            else:
                self._run_cdt_build()
        except Exception as e:
            self.build_finished.emit(False, f"构建失败: {str(e)}")
    
    def _run_make_build(self):
         if not self.project_path:
             self.build_finished.emit(False, "未选择项目路径")
             return
         
         project_name = os.path.basename(self.project_path)
         self.build_progress.emit(f"开始编译项目: {project_name:<20}")
         self.build_progress.emit(f"配置模式:    {self.config_mode:<15}")
         
         makefile_dir = os.path.join(self.project_path, self.config_mode)
         if not os.path.exists(makefile_dir):
             self.build_finished.emit(False, f"Makefile目录不存在: {makefile_dir}")
             return
         
         makefile_path = os.path.join(makefile_dir, "makefile")
         if not os.path.exists(makefile_path):
             self.build_finished.emit(False, f"Makefile不存在: {makefile_path}")
             return
         
         cmd = ["make", "-r", "-j", "all"]
         if hasattr(self, 'is_clean') and self.is_clean:
             cmd = ["make", "clean"]
         
         self.build_progress.emit(f"执行命令:    {' '.join(cmd)}")
         
         self._execute_build_command(cmd, makefile_dir)
    
    def _rename_firmware_after_make_build(self):
        try:
            makefile_dir = os.path.join(self.project_path, self.config_mode)
            project_name = os.path.basename(self.project_path)
            
            original_firmware = os.path.join(makefile_dir, f"{project_name}.bin")
            if os.path.exists(original_firmware):
                # Extract project name part after underscore if exists
                if '_' in project_name:
                    project_name_part = project_name.split('_', 1)[1]  # Take part after first underscore
                else:
                    project_name_part = project_name
                
                # Create new firmware name using project name part and scheme name
                new_firmware_name = f"{project_name_part}_{self.scheme_name}.bin"
                new_firmware = os.path.join(makefile_dir, new_firmware_name)
                
                if os.path.exists(new_firmware):
                    os.remove(new_firmware)
                
                os.rename(original_firmware, new_firmware)
                self.build_progress.emit(f"固件重命名: {project_name}.bin -> {new_firmware_name}")
                    
        except Exception as e:
            self.build_progress.emit(f"固件重命名失败: {str(e)}")
    
    def _execute_build_command(self, cmd, cwd=None):
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='gbk',
            errors='ignore',
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                if self.should_show_line(line):
                    self.build_progress.emit(line)
        
        return_code = process.poll()
        if return_code == 0:
            # Check if this is a make build and rename firmware if needed
            if hasattr(self, 'is_make') and self.is_make and hasattr(self, 'scheme_name') and self.scheme_name:
                self._rename_firmware_after_make_build()
            self.build_finished.emit(True, "编译成功")
        else:
            self.build_finished.emit(False, f"编译失败，返回码: {return_code}")
    
    def _run_cdt_build(self):
        if not self.project_path:
            self.build_finished.emit(False, "未选择项目路径")
            return
        
        if not os.path.exists(self.ide_path):
            self.build_finished.emit(False, f"MCUXpresso IDE不存在: {self.ide_path}")
            return

        project_name = os.path.basename(self.project_path)

        self.build_progress.emit(f"开始编译项目: {project_name:<20}")
        self.build_progress.emit(f"配置模式:    {self.config_mode:<15}")

        if hasattr(self, 'is_rebuild') and self.is_rebuild:
            cmd = [
                self.ide_path,
                "-nosplash",
                "-application", "org.eclipse.cdt.managedbuilder.core.headlessbuild",
                "-data", self.workspace_path,
                "-cleanBuild", f"{project_name}/{self.config_mode}",
                "-no-indexer",
            ]
        else:
            cmd = [
                self.ide_path,
                "-nosplash",
                "-application", "org.eclipse.cdt.managedbuilder.core.headlessbuild",
                "-data", self.workspace_path,
                "-build", f"{project_name}/{self.config_mode}",
                "-no-indexer",
            ]

        self.build_progress.emit(f"执行命令:    {' '.join(cmd)}")
        
        self._execute_build_command(cmd)

class HeaderGeneratorThread(QThread):
    generation_finished = pyqtSignal(bool, str) 
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = ""
        self.project_config_path = ""
    
    def setup_generation_with_mode(self, mode_key: str, config_manager, project_path: str = ""):
        self.mode_key = mode_key
        self.config_manager = config_manager
        self.project_path = project_path
        
        if project_path:
            root_dir = os.path.dirname(os.path.dirname(project_path))
            root_name = os.path.basename(root_dir)
            
            if "utn" in root_name.lower() or "32" in root_name:
                demos_dir = os.path.join(root_dir, "demos", "SE051W", "demo_transit", "inc")
            else:
                demos_dir = os.path.join(root_dir, "demos", "SR150_SE051W", "demo_transit", "inc")
            
            if os.path.exists(demos_dir):
                self.project_config_path = os.path.join(demos_dir, "project_config.h")
    
    def run(self):
        try:
            success = self._generate_project_config()
            
            if success:
                self.generation_finished.emit(True, "项目配置文件生成成功")
            else:
                self.generation_finished.emit(False, "项目配置文件生成失败")
                
        except Exception as e:
            self.generation_finished.emit(False, f"生成项目配置文件时发生错误: {str(e)}")
    
    def _generate_project_config(self) -> bool:
        try:
            if not (hasattr(self, 'mode_key') and hasattr(self, 'config_manager')):
                print("错误: 缺少新模式系统的必要属性 (mode_key 或 config_manager)")
                return False
            
            content = """#ifndef PROJECT_CONFIG_H
#define PROJECT_CONFIG_H

"""
            
            mode_macros = self.config_manager.get_mode_macros(self.mode_key)
            mode_config = self.config_manager.get_mode_config(self.mode_key)
            
            content += f"\n"
            
            for macro_name, macro_value in mode_macros.items():
                if isinstance(macro_value, str):
                    content += f"#define {macro_name} {macro_value}\n"
                elif macro_value:
                    content += f"#define {macro_name}\n"
                else:
                    content += f"//#define {macro_name}\n"
            
            content += "\n#endif /* PROJECT_CONFIG_H */\n"
            
            os.makedirs(os.path.dirname(self.project_config_path), exist_ok=True)
            
            with open(self.project_config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"生成 project_config.h 失败: {e}")
            return False