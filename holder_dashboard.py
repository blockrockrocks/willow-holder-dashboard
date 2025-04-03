
import pandas as pd
from algosdk.v2client.indexer import IndexerClient
import streamlit as st

# === CONFIGURATION ===
WILLOW_ASSET_ID = 2586029159  # Your actual WILLOW asset ID
TOTAL_SUPPLY = 1_000_000_000_000  # 1 trillion WILLOW
DECIMALS = 6
indexer_client = IndexerClient("", "https://mainnet-idx.algonode.cloud")

# === Load WILLOW Holders ===
def get_all_willow_holders(asset_id, limit=200):
    accounts = []
    next_token = None
    while True:
        response = indexer_client.accounts(limit=100, next_page=next_token, asset_id=asset_id)
        accounts.extend(response.get('accounts', []))
        next_token = response.get('next-token', None)
        if not next_token or len(accounts) >= limit:
            break
    return accounts[:limit]

# === Build leaderboard ===
def build_leaderboard(accounts):
    data = []
    for acc in accounts:
        addr = acc["address"]
        raw_amount = next((a['amount'] for a in acc.get('assets', []) if a['asset-id'] == WILLOW_ASSET_ID), 0)
        full_amount = raw_amount / 10**DECIMALS
        percent = (full_amount / TOTAL_SUPPLY) * 100
        data.append({
            "Wallet": addr,
            "WILLOW Balance": round(full_amount, 2),
            "% of Supply": round(percent, 6)
        })
    df = pd.DataFrame(data)
    df = df.sort_values("WILLOW Balance", ascending=False).reset_index(drop=True)
    df.index += 1  # Start rank at 1

    # Add allo.info links
    df["Wallet"] = df["Wallet"].apply(
        lambda x: f'<a href="https://allo.info/account/{x}" target="_blank">{x}</a>'
    )
    return df

# === Streamlit UI ===
st.set_page_config(page_title="Willow Holder Dashboard", layout="centered")
st.title("🌿 Willow Holder Dashboard")
st.caption("Track $WILLOW holdings and your rank in real time")

st.info("🔄 Fetching top WILLOW holders...")

accounts = get_all_willow_holders(WILLOW_ASSET_ID, limit=200)
leaderboard_df = build_leaderboard(accounts)

st.subheader("🏆 Leaderboard (Top 50)")
st.write(leaderboard_df.head(50).to_html(escape=False, index=True), unsafe_allow_html=True)

# === Wallet check ===
st.subheader("🔍 Check Your Wallet")

wallet_to_check = st.text_input("Enter your Algorand wallet address")
if wallet_to_check:
    leaderboard_df["PlainWallet"] = leaderboard_df["Wallet"].str.extract(r'account/(.*)"')
    match = leaderboard_df[leaderboard_df["PlainWallet"] == wallet_to_check]
    if not match.empty:
        rank = match.index[0]
        balance = match["WILLOW Balance"].values[0]
        supply_pct = match["% of Supply"].values[0]
        st.success(
            f"✅ Wallet found!\n\n🏅 Rank: #{rank}\n💰 Balance: {balance:,.2f} WILLOW\n📊 Share: {supply_pct:.6f}%"
        )
    else:
        st.warning("Wallet not found among top holders (limit: 200).")
