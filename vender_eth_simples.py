#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VENDEDOR SIMPLES DE ETHEREUM
Script para vender Ethereum com opções pré-definidas
"""

from binance.client import Client
from datetime import datetime
from logger import createLogOrder

# Suas chaves da API
api_key = "Kt8RNpiQFYakGn2JLnMKrnFC3EHAtPRppctbcQLal9jv0yuUpuptAqoXFG5Y3Dvk"
secret_key = "nMmjpjFAqW4YZloSiFXWBIdNzwcumMZgHyhFQfbgmLNNozDDcb46riqYfQOduyFh"

def vender_ethereum_simples():
    print("💰 VENDEDOR SIMPLES DE ETHEREUM")
    print("=" * 40)
    
    try:
        # Conecta com a Binance
        client = Client(api_key, secret_key)
        print("✅ Conectado à Binance!")
        
        # Busca saldo de Ethereum
        account_info = client.get_account()
        eth_balance = 0.0
        
        for balance in account_info['balances']:
            if balance['asset'] == 'ETH':
                eth_balance = float(balance['free'])
                break
        
        if eth_balance < 0.0001:
            print("❌ Saldo insuficiente para venda!")
            return
        
        # Busca preço atual
        ticker = client.get_symbol_ticker(symbol="ETHBRL")
        current_price = float(ticker['price'])
        total_value = eth_balance * current_price
        
        print(f"\n📊 SEU SALDO:")
        print(f"⟠ Ethereum: {eth_balance:.6f} ETH")
        print(f"💰 Valor total: R$ {total_value:,.2f}")
        print(f"📈 Preço atual: R$ {current_price:,.2f}")
        
        # Verifica valor mínimo da Binance (R$ 10,00)
        min_value = 10.00
        
        # Opções de venda (apenas as que atendem ao valor mínimo)
        print(f"\n🎯 OPÇÕES DE VENDA:")
        print(f"   ⚠️  Valor mínimo da Binance: R$ {min_value:.2f}")
        
        if total_value * 0.20 >= min_value:
            print(f"1. Vender 20% (R$ {total_value * 0.20:,.2f})")
        if total_value * 0.30 >= min_value:
            print(f"2. Vender 30% (R$ {total_value * 0.30:,.2f})")
        if total_value * 0.50 >= min_value:
            print(f"3. Vender 50% (R$ {total_value * 0.50:,.2f})")
        if total_value * 0.75 >= min_value:
            print(f"4. Vender 75% (R$ {total_value * 0.75:,.2f})")
        if total_value >= min_value:
            print(f"5. Vender 100% (R$ {total_value:,.2f})")
        
        print("6. Vender valor personalizado")
        
        try:
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1" and total_value * 0.20 >= min_value:
                percentage = 0.20
                quantity_to_sell = eth_balance * percentage
                value_to_sell = total_value * percentage
            elif opcao == "2" and total_value * 0.30 >= min_value:
                percentage = 0.30
                quantity_to_sell = eth_balance * percentage
                value_to_sell = total_value * percentage
            elif opcao == "3" and total_value * 0.50 >= min_value:
                percentage = 0.50
                quantity_to_sell = eth_balance * percentage
                value_to_sell = total_value * percentage
            elif opcao == "4" and total_value * 0.75 >= min_value:
                percentage = 0.75
                quantity_to_sell = eth_balance * percentage
                value_to_sell = total_value * percentage
            elif opcao == "5" and total_value >= min_value:
                percentage = 1.00
                quantity_to_sell = eth_balance
                value_to_sell = total_value
            elif opcao == "6":
                # Valor personalizado
                value_input = input(f"Digite o valor em reais para vender (mínimo R$ {min_value:.2f}, máximo R$ {total_value:,.2f}): ")
                value_to_sell = float(value_input)
                
                if value_to_sell > total_value:
                    print("❌ Valor maior que o saldo disponível!")
                    return
                
                if value_to_sell < min_value:
                    print(f"❌ Valor menor que o mínimo da Binance (R$ {min_value:.2f})!")
                    return
                
                quantity_to_sell = value_to_sell / current_price
                percentage = value_to_sell / total_value
            else:
                print("❌ Opção inválida!")
                return
            
            # Confirma a venda
            print(f"\n⚠️  CONFIRMAÇÃO DA VENDA:")
            print(f"   Quantidade: {quantity_to_sell:.6f} ETH")
            print(f"   Valor: R$ {value_to_sell:,.2f}")
            print(f"   Porcentagem: {percentage*100:.1f}%")
            print(f"   Preço: R$ {current_price:,.2f}")
            
            confirmacao = input("\nConfirma a venda? (s/n): ").lower().strip()
            
            if confirmacao in ['s', 'sim', 'y', 'yes']:
                # Executa a venda
                print(f"\n🔄 Executando venda de {quantity_to_sell:.6f} ETH...")
                
                # Formata a quantidade corretamente para a API (incremento de 0.00010000)
                import math
                step_size = 0.00010000
                quantity_formatted = math.floor(quantity_to_sell / step_size) * step_size
                
                # Se a quantidade formatada for 0, usa o saldo arredondado para baixo
                if quantity_formatted == 0:
                    quantity_formatted = math.floor(eth_balance / step_size) * step_size
                
                quantity_formatted = f"{quantity_formatted:.6f}".rstrip('0').rstrip('.')
                print(f"   Quantidade formatada: {quantity_formatted}")
                
                order = client.create_order(
                    symbol="ETHBRL",
                    side="SELL",
                    type="MARKET",
                    quantity=quantity_formatted
                )
                
                print("✅ Venda executada com sucesso!")
                print(f"📄 Ordem ID: {order['orderId']}")
                
                # Salva o log
                print("📝 Salvando log da venda...")
                createLogOrder(order)
                print("✅ Log salvo!")
                
                # Mostra o resultado
                print(f"\n🎉 VENDA CONCLUÍDA!")
                print(f"   Quantidade vendida: {float(order['executedQty']):.6f} ETH")
                print(f"   Valor recebido: R$ {float(order['cummulativeQuoteQty']):,.2f}")
                print(f"   Preço médio: R$ {float(order['cummulativeQuoteQty']) / float(order['executedQty']):,.2f}")
                
                # Mostra saldo restante
                remaining_eth = eth_balance - float(order['executedQty'])
                if remaining_eth > 0:
                    print(f"   Ethereum restante: {remaining_eth:.6f} ETH")
                
            else:
                print("❌ Venda cancelada!")
                
        except ValueError:
            print("❌ Valor inválido!")
        except KeyboardInterrupt:
            print("\n❌ Operação cancelada pelo usuário!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    vender_ethereum_simples()
