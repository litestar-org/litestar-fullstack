import { createClientConfig } from '../core/config';
import { client } from '../client.gen';
import { accountLogin, accountLogout, accountProfile } from '../sdk.gen';
import type { AccountLogin, User } from '../types.gen';

export class AccessService {
  constructor() {
    // Initialize client with config
    client.setConfig(createClientConfig({}));
  }

  async login(email: string, password: string): Promise<User> {
    const request: AccountLogin = {
      username: email,
      password,
    };
    const response = await accountLogin({ body: request });
    return response;
  }

  async logout(): Promise<void> {
    await accountLogout();
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      return await accountProfile();
    } catch (error) {
      return null;
    }
  }
}
