#!/usr/bin/env python3
"""
Script principal para executar todos os processos de limpeza de dados
"""

import subprocess
import sys
import os

def run_script(script_name):
    """Executa um script Python e retorna o código de saída"""
    print(f"\n=== EXECUTANDO {script_name} ===")
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar {script_name}:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"ERRO: Script {script_name} não encontrado")
        return False

def main():
    """Função principal"""
    print("=== INICIANDO PIPELINE DE LIMPEZA DE DADOS ===")
    
    # Lista de scripts para executar em ordem
    scripts = [
        "etl01",  # Limpeza de filmes (script original)
        "usuarios_cleaning.py",  # Limpeza de usuários
        "avaliacoes_cleaning.py"  # Limpeza de avaliações
    ]
    
    success_count = 0
    total_scripts = len(scripts)
    
    for script in scripts:
        if run_script(script):
            success_count += 1
            print(f"✅ {script} executado com sucesso")
        else:
            print(f"❌ {script} falhou")
    
    print(f"\n=== RESUMO FINAL ===")
    print(f"Scripts executados com sucesso: {success_count}/{total_scripts}")
    
    if success_count == total_scripts:
        print("🎉 TODOS OS PROCESSOS DE LIMPEZA CONCLUÍDOS COM SUCESSO!")
        return 0
    else:
        print("⚠️ ALGUNS PROCESSOS FALHARAM")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)