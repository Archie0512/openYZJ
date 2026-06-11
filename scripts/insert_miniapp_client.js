db.api_clients.insertOne({
  client_id: 'miniapp_h5',
  client_name: 'miniapp frontend',
  api_key: 'miniapp_client_2024',
  api_secret_encrypted: '',
  allowed_endpoints: [],
  rate_limit: 200,
  status: 'active',
  created_at: new Date(),
  updated_at: new Date()
});
print('inserted miniapp_h5 client');
