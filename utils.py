import re


def parse_dext_bot_message(message: str) -> dict:
    data = {}

    pattern = r"(?P<token_name>[\w\s.()]+)\s\((?P<token_pair>[\w\/]+)\)"
    token_match = re.search(pattern, message)
    if token_match:
        token_name, token_pair = token_match.groups()
        token_name = token_name.split("\n\n")[1]
        data["token_name"] = token_name.strip()
        data["token_pair"] = token_pair.strip()

    address_match = re.search(r"Token contract:\s*(0x[a-fA-F0-9]{40})", message)
    if address_match:
        token_address = address_match.group(1)
        data["token_address"] = token_address.strip()
    return data


def parse_ttf_bot_message(message: str) -> dict:
    data = {}

    # 1. Upper block (red flags, alerts, etc.)
    caution_match = re.findall(r"⚠️(.+?)\n", message)
    if caution_match:
        data['Cautions'] = [caution.strip() for caution in caution_match]

    # 2. Key parameters
    market_cap_match = re.search(r"💰 MC: \$(\d+(\.\d+)?[KMB]?)", message)
    if market_cap_match:
        data['MC'] = market_cap_match.group(1).strip()

    liquidity_match = re.search(r"Liq: \$(\d+(\.\d+)?[KMB]?)", message)
    if liquidity_match:
        data['Liq'] = liquidity_match.group(1).strip()

    liquidity_per_match = re.search(r"\((\d+%)\)", message)
    if liquidity_per_match:
        data['Liq_%'] = liquidity_per_match.group(1).strip()

    lp_lock_match = re.search(r"🔒 LP Lock: (\d+%Unlocked|\d+%Locked), ([\w\s]+)", message)
    if lp_lock_match:
        data['LP_Lock'] = {
            'percentage': lp_lock_match.group(1).strip(),
            'platform': lp_lock_match.group(2).strip()
        }

    tax_match = re.search(r"💳 Tax: B: (\d+%) \| S: (\d+%) \| T: (\d+%)", message)
    if tax_match:
        data['Tax_Buy'] = tax_match.group(1).strip()
        data['Tax_Sell'] = tax_match.group(2).strip()
        data['Tax_Total'] = tax_match.group(3).strip()

    gas_match = re.search(r"Gas: (\d+) \| (\d+)", message)
    if gas_match:
        data['Gas'] = {'Gas1': gas_match.group(1).strip(), 'Gas2': gas_match.group(2).strip()}

    burned_match = re.search(r"Burned: (\d+%)", message)
    if burned_match:
        data['Burned'] = burned_match.group(1).strip()

    holders_match = re.search(r"Holders: (\d+)", message)
    if holders_match:
        data['Holders'] = holders_match.group(1).strip()

    top10_match = re.search(r"Top 10: ([\d\.]+%)", message)
    if top10_match:
        data['Top_10'] = top10_match.group(1).strip()

    airdrops_match = re.search(r"💸 Airdrops: (.+?)\n", message)
    if airdrops_match:
        data['Airdrops'] = airdrops_match.group(1).strip()

    return data


def generate_report(data):
    report = f"🚨 **New Token Alert**: {data['token_name']} ({data['token_pair']})\n"
    report += f"🔗 **Token Address**: {data['token_address']}\n\n"

    # Check if 'Cautions' exists
    if 'Cautions' in data and data['Cautions']:
        cautions = "\n".join(data["Cautions"])
        report += f"⚠️ **Cautions**:\n{cautions}\n\n"

    # Check if 'MC' (Market Cap) exists
    if 'MC' in data:
        report += f"💰 **Market Cap**: {data['MC']}\n"

    # Check if 'Liq' (Liquidity) exists
    if 'Liq' in data and 'Liq_%' in data:
        report += f"💧 **Liquidity**: {data['Liq']} ({data['Liq_%']})\n"

    # Check if 'LP_Lock' exists
    if 'LP_Lock' in data:
        report += f"🔒 **Liquidity Locked**: {data['LP_Lock']['percentage']} on {data['LP_Lock']['platform']}\n"

    # Check if tax information exists
    if 'Tax_Buy' in data and 'Tax_Sell' in data and 'Tax_Total' in data:
        report += f"🛒 **Buy Tax**: {data['Tax_Buy']} | **Sell Tax**: {data['Tax_Sell']} | **Total Tax**: {data['Tax_Total']}\n"

    # Check if gas information exists
    if 'Gas' in data:
        report += f"⚡ **Gas**: Gas1 - {data['Gas'].get('Gas1', 'N/A')} | Gas2 - {data['Gas'].get('Gas2', 'N/A')}\n"

    # Check if 'Burned' exists
    if 'Burned' in data:
        report += f"🔥 **Burned**: {data['Burned']}\n"

    # Check if 'Holders' exists
    if 'Holders' in data:
        report += f"👥 **Holders**: {data['Holders']} | **Top 10 Holders**: {data.get('Top_10', 'N/A')}\n"

    # Check if 'Airdrops' exists
    if 'Airdrops' in data:
        report += f"🎁 **Airdrops**: {data['Airdrops']}\n"

    # Check if 'risk' and 'riskLevel' exist
    if 'risk' in data and 'riskLevel' in data:
        report += f"⚡ **Honeypot risk**: {data['risk']} (Level: {data['riskLevel']})"

    return report
