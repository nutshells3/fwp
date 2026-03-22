export class ProtocolDriver {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  async loadFixtures() {
    const response = await fetch("../../packages/formal-protocol/examples/ui-fixtures.json");
    return await response.json();
  }

  async loadTranscript(relativePath) {
    const response = await fetch(relativePath);
    return await response.json();
  }

  async rpc(method, params) {
    if (!this.baseUrl) {
      throw new Error("HTTP hub baseUrl not configured");
    }
    const response = await fetch(this.baseUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
    });
    return await response.json();
  }
}
