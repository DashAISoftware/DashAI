export interface ICredential {
  name: string;
  display_name: string;
  description: string;
  is_authenticated: boolean;
  key: string | null;
}
