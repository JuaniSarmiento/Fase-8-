#!/usr/bin/env python3
"""
Security Audit Script
=====================
Performs automated security checks on the codebase
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

# ANSI colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

class SecurityAuditor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def log_issue(self, category: str, message: str, file: str = None, line: int = None):
        """Log a security issue"""
        issue = {
            'category': category,
            'message': message,
            'file': file,
            'line': line,
            'severity': 'high'
        }
        self.issues.append(issue)
        
    def log_warning(self, category: str, message: str, file: str = None):
        """Log a security warning"""
        warning = {
            'category': category,
            'message': message,
            'file': file,
            'severity': 'medium'
        }
        self.warnings.append(warning)
        
    def log_pass(self, category: str, message: str):
        """Log a passed check"""
        self.passed.append({'category': category, 'message': message})
    
    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets in code"""
        print(f"\n{YELLOW}[*] Checking for hardcoded secrets...{NC}")
        
        patterns = {
            'AWS Key': r'AKIA[0-9A-Z]{16}',
            'Generic API Key': r'api[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{32,}',
            'Password': r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',
            'Secret': r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',
            'Token': r'token["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{32,}',
            'Private Key': r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----',
        }
        
        exclude_patterns = [
            r'\.git/',
            r'__pycache__/',
            r'\.pyc$',
            r'node_modules/',
            r'\.env\.example',
            r'docs/',
        ]
        
        found_secrets = False
        
        for ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.env']:
            for file_path in self.project_root.rglob(f'*{ext}'):
                # Skip excluded paths
                if any(re.search(pattern, str(file_path)) for pattern in exclude_patterns):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for secret_type, pattern in patterns.items():
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                # Get line number
                                line_num = content[:match.start()].count('\n') + 1
                                self.log_issue(
                                    'Hardcoded Secrets',
                                    f'Potential {secret_type} found',
                                    str(file_path.relative_to(self.project_root)),
                                    line_num
                                )
                                found_secrets = True
                except Exception as e:
                    pass
        
        if not found_secrets:
            self.log_pass('Hardcoded Secrets', 'No hardcoded secrets found')
            
    def check_sql_injection_risks(self):
        """Check for SQL injection vulnerabilities"""
        print(f"\n{YELLOW}[*] Checking for SQL injection risks...{NC}")
        
        risky_patterns = [
            r'execute\s*\([^)]*%\s*[^)]*\)',  # String formatting in execute
            r'\.format\s*\([^)]*\)\s*\)',  # String format in queries
            r'f["\'][^"\']*SELECT[^"\']*{',  # f-strings with SQL
        ]
        
        found_risks = False
        
        for file_path in self.project_root.rglob('*.py'):
            if '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in risky_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            self.log_warning(
                                'SQL Injection',
                                'Potential SQL injection risk - use parameterized queries',
                                str(file_path.relative_to(self.project_root))
                            )
                            found_risks = True
            except Exception:
                pass
        
        if not found_risks:
            self.log_pass('SQL Injection', 'No obvious SQL injection risks found')
            
    def check_xss_risks(self):
        """Check for XSS vulnerabilities"""
        print(f"\n{YELLOW}[*] Checking for XSS risks...{NC}")
        
        risky_patterns = [
            r'dangerouslySetInnerHTML',
            r'innerHTML\s*=',
            r'document\.write\(',
        ]
        
        found_risks = False
        
        for ext in ['.js', '.jsx', '.ts', '.tsx']:
            for file_path in self.project_root.rglob(f'*{ext}'):
                if 'node_modules' in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in risky_patterns:
                            if re.search(pattern, content):
                                self.log_warning(
                                    'XSS',
                                    f'Potential XSS risk - found {pattern}',
                                    str(file_path.relative_to(self.project_root))
                                )
                                found_risks = True
                except Exception:
                    pass
        
        if not found_risks:
            self.log_pass('XSS', 'No XSS risks found')
            
    def check_environment_files(self):
        """Check for .env files in version control"""
        print(f"\n{YELLOW}[*] Checking environment files...{NC}")
        
        env_files = list(self.project_root.rglob('.env'))
        if env_files:
            for env_file in env_files:
                if '.example' not in str(env_file):
                    self.log_issue(
                        'Environment Files',
                        '.env file found - should not be in version control',
                        str(env_file.relative_to(self.project_root))
                    )
        else:
            self.log_pass('Environment Files', 'No .env files in repo')
            
        # Check .gitignore
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                content = f.read()
                if '.env' in content:
                    self.log_pass('Git Ignore', '.env is in .gitignore')
                else:
                    self.log_warning('Git Ignore', '.env should be in .gitignore', '.gitignore')
                    
    def check_debug_mode(self):
        """Check for debug mode in production configs"""
        print(f"\n{YELLOW}[*] Checking debug configurations...{NC}")
        
        production_files = [
            'docker-compose.production.yml',
            '.env.production.example',
            'Dockerfile.production'
        ]
        
        for file_name in production_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    if re.search(r'DEBUG\s*=\s*True', content, re.IGNORECASE):
                        self.log_issue(
                            'Debug Mode',
                            'DEBUG=True found in production config',
                            file_name
                        )
                    else:
                        self.log_pass('Debug Mode', f'{file_name} has DEBUG=False')
                        
    def check_cors_configuration(self):
        """Check CORS configuration"""
        print(f"\n{YELLOW}[*] Checking CORS configuration...{NC}")
        
        main_py = self.project_root / 'backend' / 'src_v3' / 'main.py'
        if main_py.exists():
            with open(main_py, 'r') as f:
                content = f.read()
                
                # Check for wildcard origins
                if re.search(r'allow_origins\s*=\s*\["?\*"?\]', content):
                    self.log_issue(
                        'CORS',
                        'Wildcard (*) in CORS origins - security risk',
                        'backend/src_v3/main.py'
                    )
                else:
                    self.log_pass('CORS', 'No wildcard in CORS origins')
                    
                # Check for allow_credentials with wildcard
                if 'allow_credentials=True' in content and '*' in content:
                    self.log_warning(
                        'CORS',
                        'allow_credentials=True with wildcard origins',
                        'backend/src_v3/main.py'
                    )
                    
    def check_password_storage(self):
        """Check password storage practices"""
        print(f"\n{YELLOW}[*] Checking password storage...{NC}")
        
        security_py = self.project_root / 'backend' / 'src_v3' / 'core' / 'security.py'
        if security_py.exists():
            with open(security_py, 'r') as f:
                content = f.read()
                
                if 'bcrypt' in content:
                    self.log_pass('Password Storage', 'Using bcrypt for password hashing')
                else:
                    self.log_warning(
                        'Password Storage',
                        'bcrypt not found in security.py',
                        'backend/src_v3/core/security.py'
                    )
                    
    def check_dependencies(self):
        """Check for known vulnerable dependencies"""
        print(f"\n{YELLOW}[*] Checking dependencies...{NC}")
        
        # This would normally use 'safety check' or similar
        # For now, just check if requirements.txt exists
        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            self.log_pass('Dependencies', 'requirements.txt found')
            print(f"  {YELLOW}→ Run 'pip install safety && safety check' for vulnerability scan{NC}")
        else:
            self.log_warning('Dependencies', 'requirements.txt not found', '/')
            
    def generate_report(self):
        """Generate security audit report"""
        print(f"\n{'='*80}")
        print(f"{GREEN}Security Audit Report{NC}")
        print(f"{'='*80}\n")
        
        # Summary
        total_checks = len(self.issues) + len(self.warnings) + len(self.passed)
        print(f"Total Checks: {total_checks}")
        print(f"{RED}Issues: {len(self.issues)}{NC}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{NC}")
        print(f"{GREEN}Passed: {len(self.passed)}{NC}\n")
        
        # Issues
        if self.issues:
            print(f"\n{RED}{'='*80}")
            print(f"ISSUES (High Severity){NC}")
            print(f"{RED}{'='*80}{NC}\n")
            for issue in self.issues:
                print(f"  {RED}✗{NC} [{issue['category']}] {issue['message']}")
                if issue['file']:
                    location = f"    📁 {issue['file']}"
                    if issue['line']:
                        location += f":{issue['line']}"
                    print(location)
                print()
        
        # Warnings
        if self.warnings:
            print(f"\n{YELLOW}{'='*80}")
            print(f"WARNINGS (Medium Severity){NC}")
            print(f"{YELLOW}{'='*80}{NC}\n")
            for warning in self.warnings:
                print(f"  {YELLOW}⚠{NC} [{warning['category']}] {warning['message']}")
                if warning['file']:
                    print(f"    📁 {warning['file']}")
                print()
        
        # Passed
        if self.passed:
            print(f"\n{GREEN}{'='*80}")
            print(f"PASSED CHECKS{NC}")
            print(f"{GREEN}{'='*80}{NC}\n")
            for passed in self.passed:
                print(f"  {GREEN}✓{NC} [{passed['category']}] {passed['message']}")
        
        # Conclusion
        print(f"\n{'='*80}")
        if len(self.issues) == 0 and len(self.warnings) == 0:
            print(f"{GREEN}✓ All security checks passed!{NC}")
            return 0
        elif len(self.issues) == 0:
            print(f"{YELLOW}⚠ Some warnings found. Review and fix before production.{NC}")
            return 1
        else:
            print(f"{RED}✗ Security issues found. Fix before deployment!{NC}")
            return 2
            
    def run_all_checks(self):
        """Run all security checks"""
        print(f"{GREEN}{'='*80}")
        print(f"Starting Security Audit{NC}")
        print(f"Project: {self.project_root}")
        print(f"{GREEN}{'='*80}{NC}")
        
        self.check_hardcoded_secrets()
        self.check_sql_injection_risks()
        self.check_xss_risks()
        self.check_environment_files()
        self.check_debug_mode()
        self.check_cors_configuration()
        self.check_password_storage()
        self.check_dependencies()
        
        return self.generate_report()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    auditor = SecurityAuditor(project_root)
    exit_code = auditor.run_all_checks()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
