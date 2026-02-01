import { type FullConfig } from '@playwright/test';
declare function globalSetup(config: FullConfig): Promise<void>;
export default globalSetup;
