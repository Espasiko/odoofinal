import axios from 'axios';

class OdooClient {
  private baseURL: string;
  private database: string;
  private username: string;
  private password: string;
  private apiKey: string;
  private uid: number | null = null;
  private session_id: string | null = null;

  constructor() {
    this.baseURL = import.meta.env.VITE_ODOO_URL || 'http://localhost:8070';
    this.database = import.meta.env.VITE_ODOO_DB || 'fresh_odoo_db';
    this.username = import.meta.env.VITE_ODOO_USERNAME || 'admin';
    this.password = import.meta.env.VITE_ODOO_PASSWORD || 'admin';
    this.apiKey = import.meta.env.VITE_ODOO_API_KEY || '7917ee3d696b77614504060c27da891e62115148';
  }

  async login(): Promise<boolean> {
    try {
      const response = await axios.post(`${this.baseURL}/web/session/authenticate`, {
        jsonrpc: '2.0',
        params: {
          db: this.database,
          login: this.username,
          password: this.password,
        },
      });

      if (response.data.result && response.data.result.uid) {
        this.uid = response.data.result.uid;
        this.session_id = response.data.result.session_id;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error en la autenticación:', error);
      return false;
    }
  }

  // Método alternativo usando API Key
  async authenticateWithApiKey(): Promise<boolean> {
    try {
      const response = await axios.post(`${this.baseURL}/web/dataset/call_kw`, {
        jsonrpc: '2.0',
        params: {
          model: 'res.users',
          method: 'search_read',
          args: [[['login', '=', this.username]], ['id', 'name']],
          kwargs: {
            context: {
              'api_key': this.apiKey
            }
          }
        }
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.result && response.data.result.length > 0) {
        this.uid = response.data.result[0].id;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error en la autenticación con API Key:', error);
      return false;
    }
  }

  async searchRead(model: string, domain: any[], fields: string[], limit: number = 0): Promise<any[]> {
    if (!this.uid) {
      await this.login();
    }

    try {
      const response = await axios.post(`${this.baseURL}/web/dataset/search_read`, {
        jsonrpc: '2.0',
        params: {
          model,
          domain,
          fields,
          limit,
        },
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Cookie': `session_id=${this.session_id}`,
        },
      });

      return response.data.result.records || [];
    } catch (error) {
      console.error('Error en search_read:', error);
      return [];
    }
  }

  async create(model: string, values: any): Promise<number> {
    if (!this.uid) {
      await this.login();
    }

    try {
      const response = await axios.post(`${this.baseURL}/web/dataset/call_kw`, {
        jsonrpc: '2.0',
        params: {
          model,
          method: 'create',
          args: [values],
          kwargs: {},
        },
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Cookie': `session_id=${this.session_id}`,
        },
      });

      return response.data.result;
    } catch (error) {
      console.error('Error en create:', error);
      return 0;
    }
  }

  async write(model: string, id: number, values: any): Promise<boolean> {
    if (!this.uid) {
      await this.login();
    }

    try {
      const response = await axios.post(`${this.baseURL}/web/dataset/call_kw`, {
        jsonrpc: '2.0',
        params: {
          model,
          method: 'write',
          args: [[id], values],
          kwargs: {},
        },
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Cookie': `session_id=${this.session_id}`,
        },
      });

      return response.data.result;
    } catch (error) {
      console.error('Error en write:', error);
      return false;
    }
  }

  async unlink(model: string, id: number): Promise<boolean> {
    if (!this.uid) {
      await this.login();
    }

    try {
      const response = await axios.post(`${this.baseURL}/web/dataset/call_kw`, {
        jsonrpc: '2.0',
        params: {
          model,
          method: 'unlink',
          args: [[id]],
          kwargs: {},
        },
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Cookie': `session_id=${this.session_id}`,
        },
      });

      return response.data.result;
    } catch (error) {
      console.error('Error en unlink:', error);
      return false;
    }
  }
}

export default OdooClient;