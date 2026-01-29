"""
检索所有永续合约的当前资金费率。
显示哪些资产有正资金费率（永续合约支付给现货持有者）。
"""

import asyncio
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import httpx
from hyperliquid.info import Info

load_dotenv()

BASE_URL = os.getenv("HYPERLIQUID_PUBLIC_BASE_URL")
MIN_FUNDING_RATE = 0.0001  # 0.01%最小阈值


async def get_funding_rates_sdk() -> Optional[List[Dict]]:
    """方法1：使用Hyperliquid Python SDK"""
    print("Method 1: Hyperliquid SDK")
    print("-" * 30)

    try:
        info = Info(BASE_URL, skip_ws=True)
        meta_and_contexts = info.meta_and_asset_ctxs()
        
        funding_opportunities = []
        
        if meta_and_contexts and len(meta_and_contexts) >= 2:
            meta = meta_and_contexts[0]
            asset_ctxs = meta_and_contexts[1]

            # 通过索引将universe中的资产名称映射到contexts
            for i, asset_ctx in enumerate(asset_ctxs):
                asset_name = meta["universe"][i]["name"] if i < len(meta["universe"]) else f"UNKNOWN_{i}"
                funding_rate = float(asset_ctx.get("funding", "0"))
                mark_price = float(asset_ctx.get("markPx", "0"))
                
                if funding_rate > MIN_FUNDING_RATE:
                    funding_opportunities.append({
                        "asset": asset_name,
                        "funding_rate": funding_rate,
                        "funding_rate_pct": funding_rate * 100,
                        "annual_rate_pct": funding_rate * 100 * 365 * 24,  # 每天24次支付
                        "mark_price": mark_price
                    })
            
            funding_opportunities.sort(key=lambda x: x["funding_rate"], reverse=True)
            
            print(f"Found {len(funding_opportunities)} positive funding opportunities")
            print()
            
            for i, opp in enumerate(funding_opportunities[:10], 1):
                print(f"{i:2d}. {opp['asset']:>6}: {opp['funding_rate_pct']:+7.4f}% "
                      f"(Annual: {opp['annual_rate_pct']:+7.1f}%) @ ${opp['mark_price']:,.2f}")
            
            return funding_opportunities
        
        return None

    except Exception as e:
        print(f"SDK method failed: {e}")
        return None


async def get_funding_rates_raw() -> Optional[List[Dict]]:
    """方法2：原始HTTP API调用"""
    print("\nMethod 2: Raw HTTP API")
    print("-" * 30)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/info",
                json={"type": "metaAndAssetCtxs"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                funding_opportunities = []
                
                if len(data) >= 2:
                    meta = data[0]
                    asset_ctxs = data[1]

                    # 通过索引将universe中的资产名称映射到contexts
                    for i, asset_ctx in enumerate(asset_ctxs):
                        asset_name = meta["universe"][i]["name"] if i < len(meta["universe"]) else f"UNKNOWN_{i}"
                        funding_rate = float(asset_ctx.get("funding", "0"))
                        mark_price = float(asset_ctx.get("markPx", "0"))
                        
                        if funding_rate > MIN_FUNDING_RATE:
                            funding_opportunities.append({
                                "asset": asset_name,
                                "funding_rate": funding_rate,
                                "funding_rate_pct": funding_rate * 100,
                                "annual_rate_pct": funding_rate * 100 * 365 * 24,
                                "mark_price": mark_price
                            })
                    
                    funding_opportunities.sort(key=lambda x: x["funding_rate"], reverse=True)
                    
                    print(f"Found {len(funding_opportunities)} positive funding opportunities")
                    print()
                    
                    for i, opp in enumerate(funding_opportunities[:10], 1):
                        print(f"{i:2d}. {opp['asset']:>6}: {opp['funding_rate_pct']:+7.4f}% "
                              f"(Annual: {opp['annual_rate_pct']:+7.1f}%) @ ${opp['mark_price']:,.2f}")
                    
                    return funding_opportunities
            else:
                print(f"HTTP failed: {response.status_code}")
                return None

    except Exception as e:
        print(f"HTTP method failed: {e}")
        return None


async def get_predicted_fundings() -> Optional[Dict]:
    """获取跨交易所的预测资金费率"""
    print("\nPredicted Funding Rates (Cross-Exchange)")
    print("-" * 45)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/info",
                json={"type": "predictedFundings"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                predicted_fundings = response.json()

                # 处理基于列表的响应格式
                if isinstance(predicted_fundings, list):
                    hl_positive_fundings = []
                    
                    for item in predicted_fundings:
                        if len(item) >= 2:
                            asset_name = item[0]
                            exchange_data = item[1]
                            
                            for exchange_info in exchange_data:
                                if len(exchange_info) >= 2:
                                    exchange_name = exchange_info[0]
                                    exchange_details = exchange_info[1]
                                    
                                    if exchange_name == 'HlPerp' and exchange_details and 'fundingRate' in exchange_details:
                                        funding_rate = float(exchange_details['fundingRate'])
                                        if funding_rate > MIN_FUNDING_RATE:
                                            hl_positive_fundings.append((asset_name, funding_rate))

                    # 显示Hyperliquid正资金费率
                    if hl_positive_fundings:
                        hl_positive_fundings.sort(key=lambda x: x[1], reverse=True)
                        print("Hyperliquid Perp - Top positive funding rates:")
                        for asset, rate in hl_positive_fundings[:10]:
                            print(f"   {asset:>8}: {rate*100:+7.4f}%")
                    else:
                        print("No positive funding opportunities found")
                
                else:
                    print(f"Unexpected API response format: {type(predicted_fundings)}")
                
                return predicted_fundings
            else:
                print(f"HTTP failed: {response.status_code}")
                return None

    except Exception as e:
        print(f"Predicted fundings failed: {e}")
        return None


def calculate_profit_potential(funding_rate: float, position_value: float, hours_held: int = 1) -> Dict:
    """
    计算现货多头 + 永续合约空头资金费率套利的潜在利润

    策略：买入现货资产，在永续合约上做空等量
    - 收取正资金费率支付（费率>0时永续合约空头收取资金费）
    - 市场中性（现货多头对冲永续合约空头的价格风险）
    """
    funding_payments = hours_held
    gross_profit = funding_rate * position_value * funding_payments

    # 估算现货-永续合约套利的交易费用：
    # - 买入现货：~0.040% taker费用
    # - 做空永续合约：~0.015% taker费用
    # - 卖出现货：~0.040% taker费用（退出）
    # - 平仓永续合约：~0.015% taker费用（退出）
    estimated_fees = position_value * 0.0011  # 总计~0.11%
    net_profit = gross_profit - estimated_fees
    
    return {
        "funding_payments": funding_payments,
        "gross_profit": gross_profit,
        "estimated_fees": estimated_fees,
        "net_profit": net_profit,
        "net_profit_pct": (net_profit / position_value) * 100
    }


async def main():
    print("Hyperliquid Funding Rate Discovery")
    print("=" * 50)

    sdk_rates = await get_funding_rates_sdk()
    raw_rates = await get_funding_rates_raw()
    predicted = await get_predicted_fundings()

    if sdk_rates:
        print("\nSpot-Perp Funding Arbitrage Analysis ($10,000 position)")
        print("-" * 60)
        print("Strategy: Long spot + Short perp (market neutral)")
        
        for opp in sdk_rates[:3]:
            profit_1h = calculate_profit_potential(opp["funding_rate"], 10000, 1)
            print(f"\n{opp['asset']} (Funding: {opp['funding_rate_pct']:+.4f}%):")
            print(f"   1h profit: ${profit_1h['net_profit']:+.2f} ({profit_1h['net_profit_pct']:+.3f}%)")


if __name__ == "__main__":
    asyncio.run(main())