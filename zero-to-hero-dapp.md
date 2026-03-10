---
task_id: zero-to-hero-dapp
title: "Zero to Hero Smart Contract DApp"
objective: "Set up a Hardhat project, create and deploy a Storage smart contract to Polkadot Hub TestNet, then build a Next.js dApp with Viem that connects a wallet, reads on-chain data, and writes transactions."
prerequisites: ["Node.js v22.10.0 or later", "npm", "Polkadot Hub TestNet RPC endpoint: https://services.polkadothub-rpc.com/testnet", "Chain ID: 420420417", "Test PAS tokens from the Polkadot faucet (https://faucet.polkadot.io/)", "MetaMask or compatible Ethereum wallet with an exported private key"]
estimated_steps: 16
reference_repo: https://github.com/polkadot-developers/revm-hardhat-examples
generated: 2026-03-09T21:52:21Z
---

# Zero to Hero Smart Contract DApp

**Objective:** Set up a Hardhat project, create and deploy a Storage smart contract to Polkadot Hub TestNet, then build a Next.js dApp with Viem that connects a wallet, reads on-chain data, and writes transactions.

## Prerequisites

**Runtime:**
- Node.js v22.10.0 or later
- npm

**Network:**
- Polkadot Hub TestNet RPC endpoint: https://services.polkadothub-rpc.com/testnet
- Chain ID: 420420417

**Tokens:**
- Test PAS tokens from the Polkadot faucet (https://faucet.polkadot.io/)

**Wallet:**
- MetaMask or compatible Ethereum wallet with an exported private key

## Environment Variables

Create a `.env` file in your project root:

```env
# Wallet private key for signing contract deployment transactions. Export from MetaMask or another Ethereum-compatible wallet. (required)
PRIVATE_KEY=
```

## Execution Steps

### Step 1: Create the project root directory

```bash
mkdir polkadot-hub-tutorial
cd polkadot-hub-tutorial
```

### Step 2: Initialize the Hardhat project

This command is interactive. When prompted, select 'Create a TypeScript project' and accept all default options. If running non-interactively, you may need to pipe input or use flags to bypass prompts.

```bash
mkdir storage-contract
cd storage-contract
npm init -y
npm install --save-dev hardhat@3.0.9
npx hardhat --init
```

### Step 3: Create the Storage smart contract

Delete any default contract files in the contracts/ directory, then fetch the reference file and save it as contracts/Storage.sol. This contract stores a uint256, emits a NumberStored event on update, and exposes a public storedNumber getter.

**Reference file:** [`storage-contract/contracts/Storage.sol`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/storage-contract/contracts/Storage.sol)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 4: Configure Hardhat for Polkadot Hub TestNet

Replace the generated hardhat.config.ts entirely with the fetched reference file. It includes the polkadotTestNet network configuration using the RPC URL and process.env.PRIVATE_KEY. Also create a .env file in the storage-contract directory with PRIVATE_KEY=<your-private-key>.

**Reference file:** [`storage-contract/hardhat.config.ts`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/storage-contract/hardhat.config.ts)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 5: Compile the Storage contract

```bash
npx hardhat compile
```

**Expected output:** Successfully compiled 1 Solidity file

### Step 6: Create the Hardhat Ignition deployment module

Delete any default files in the ignition/modules/ directory, then fetch the reference file and save it as ignition/modules/Storage.ts. It defines a StorageModule that deploys the Storage contract.

**Reference file:** [`storage-contract/ignition/modules/Storage.ts`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/storage-contract/ignition/modules/Storage.ts)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 7: Deploy the contract to Polkadot Hub TestNet

This command is interactive — it will prompt 'Confirm deploy to network polkadotTestNet (420420417)?' and you must respond 'yes'. Save the deployed contract address from the output (e.g., StorageModule#Storage - 0x...) — you will need it in step 11.

```bash
npx hardhat ignition deploy ./ignition/modules/Storage.ts --network polkadotTestNet
```

**Expected output:** [ StorageModule ] successfully deployed. Deployed Addresses: StorageModule#Storage - 0x...

### Step 8: Create the Next.js dApp project

Navigate back to the project root (polkadot-hub-tutorial) before running create-next-app.

```bash
cd ..
npx create-next-app dapp --ts --eslint --tailwind --app --yes
cd dapp
npm install viem@2.38.5
npm install --save-dev typescript@5.9.3 @types/node@22.19.24
```

### Step 9: Create the Viem client configuration

Fetch the reference file and save it as viem.ts in the dapp project root (dapp/viem.ts, not inside app/). This file defines the Polkadot Hub TestNet chain, creates a public client for reading data, and provides a getWalletClient function for signing transactions. Other files import from this path.

**Reference file:** [`dapp/viem.ts`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/viem.ts)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 10: Copy the contract ABI to the dApp

Copy the ABI JSON generated by Hardhat compilation into the dApp's abis directory so the frontend can import it.

```bash
mkdir -p abis
cp ../storage-contract/artifacts/contracts/Storage.sol/Storage.json ./abis/Storage.json
```

### Step 11: Create the contract interface utility

Fetch the reference file and save it as utils/contract.ts (at dapp/utils/contract.ts). Important: the reference file contains a hardcoded contract address. You must replace that address with the actual contract address you saved from the deployment output in step 7.

**Reference file:** [`dapp/utils/contract.ts`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/utils/contract.ts)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 12: Create the WalletConnect component

Fetch the reference file and save it as app/components/WalletConnect.tsx. This component handles MetaMask wallet connection, network switching to Polkadot Hub TestNet, and displays the connected account.

**Reference file:** [`dapp/app/components/WalletConnect.tsx`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/components/WalletConnect.tsx)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 13: Create the ReadContract component

Fetch the reference file and save it as app/components/ReadContract.tsx. This component reads the storedNumber value from the contract using viem's readContract and polls for updates every 10 seconds.

**Reference file:** [`dapp/app/components/ReadContract.tsx`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/components/ReadContract.tsx)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 14: Create the WriteContract component

Fetch the reference file and save it as app/components/WriteContract.tsx. This component allows users to input a number and send a setNumber transaction, with simulation, wallet signing, and receipt confirmation.

**Reference file:** [`dapp/app/components/WriteContract.tsx`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/components/WriteContract.tsx)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 15: Update the main page to integrate all components

Fetch the reference file and replace the generated app/page.tsx. This file imports and renders WalletConnect, ReadContract, and WriteContract components with shared account state.

**Reference file:** [`dapp/app/page.tsx`](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/page.tsx)

Fetch this file and adapt it to your project. See the Reference Code Index below for a description of what this file does.

### Step 16: Run the dApp

```bash
npm run dev
```

**Expected output:** The dApp is available at http://localhost:3000 with a wallet connection button, stored number display, and update form.

## Reference Code Index

These files are from [revm-hardhat-examples](https://github.com/polkadot-developers/revm-hardhat-examples) (`zero-to-hero-dapp` directory). Fetch them as needed — do not download all files upfront.

| File | Description | Raw URL |
|---|---|---|
| `storage-contract/contracts/Storage.sol` | Solidity contract that stores a uint256, emits NumberStored event on update, and exposes a public storedNumber getter | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/storage-contract/contracts/Storage.sol) |
| `storage-contract/hardhat.config.ts` | Hardhat configuration with Polkadot Hub TestNet network settings (chain ID 420420417) | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/storage-contract/hardhat.config.ts) |
| `storage-contract/ignition/modules/Storage.ts` | Hardhat Ignition deployment module for the Storage contract | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/storage-contract/ignition/modules/Storage.ts) |
| `dapp/viem.ts` | Viem client setup with Polkadot Hub TestNet chain config, public client, and wallet client factory | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/viem.ts) |
| `dapp/utils/contract.ts` | Contract address, ABI import, and helper functions to get read-only and signer contract instances | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/utils/contract.ts) |
| `dapp/abis/Storage.json` | Contract ABI JSON copied from Hardhat build artifacts | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/abis/Storage.json) |
| `dapp/app/components/WalletConnect.tsx` | React component handling MetaMask connection, account tracking, and Polkadot Hub TestNet network switching | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/components/WalletConnect.tsx) |
| `dapp/app/components/ReadContract.tsx` | React component that reads storedNumber from the contract and polls for updates | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/components/ReadContract.tsx) |
| `dapp/app/components/WriteContract.tsx` | React component with form input to call setNumber, including simulation, signing, and receipt handling | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/components/WriteContract.tsx) |
| `dapp/app/page.tsx` | Main Next.js page composing WalletConnect, ReadContract, and WriteContract with shared account state | [Fetch](https://raw.githubusercontent.com/polkadot-developers/revm-hardhat-examples/master/zero-to-hero-dapp/dapp/app/page.tsx) |

## Error Recovery

**`ProviderError: insufficient funds`**
- **Cause:** The wallet does not have enough test PAS tokens to cover gas fees for deployment or transactions.
- **Resolution:** Request test tokens from the Polkadot faucet at https://faucet.polkadot.io/ and ensure the correct account is funded.

**`HardhatError: HH108: Cannot connect to the network`**
- **Cause:** The Polkadot Hub TestNet RPC endpoint is unreachable or the URL is misconfigured.
- **Resolution:** Verify the RPC URL is https://services.polkadothub-rpc.com/testnet and that you have network connectivity.

**`Error: No Ethereum browser provider detected`**
- **Cause:** The dApp is running in a browser without MetaMask or a compatible wallet extension installed.
- **Resolution:** Install MetaMask browser extension and refresh the page.

**`Error 4902: Unrecognized chain ID`**
- **Cause:** Polkadot Hub TestNet has not been added to the user's MetaMask wallet.
- **Resolution:** The WalletConnect component handles this automatically by calling wallet_addEthereumChain. If it persists, manually add the network in MetaMask with chain ID 420420417.

**`Error: Account not found on current network`**
- **Cause:** The wallet is connected to a different network than Polkadot Hub TestNet.
- **Resolution:** Switch to Polkadot Hub TestNet in MetaMask or use the 'Switch to Polkadot Testnet' button in the dApp.

**`PRIVATE_KEY is not set or is empty`**
- **Cause:** The .env file is missing or the PRIVATE_KEY variable is not set.
- **Resolution:** Create a .env file in the storage-contract directory with PRIVATE_KEY=<your-private-key>. Export your private key from MetaMask under Account Details.

## Supplementary Context

These resolved documentation pages provide deeper context on wallet setup, network configuration, and smart contract fundamentals. Consult them if you need to understand why a step works, not just how to execute it.

- [smart-contracts-connect](https://docs.polkadot.com/ai/pages/smart-contracts-connect.md) — Network connection details, chain IDs, RPC URLs, and wallet configuration for Polkadot Hub TestNet and MainNet
- [smart-contracts-faucet](https://docs.polkadot.com/ai/pages/smart-contracts-faucet.md) — How to obtain test PAS tokens needed for gas fees during contract deployment and transactions
- [smart-contracts-cookbook-smart-contracts-deploy-basic-basic-hardhat](https://docs.polkadot.com/ai/pages/smart-contracts-cookbook-smart-contracts-deploy-basic-basic-hardhat.md) — Detailed walkthrough of Hardhat project setup and basic contract deployment, useful if the agent needs more context on Hardhat configuration
