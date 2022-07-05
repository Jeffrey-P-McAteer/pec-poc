
# Builtin libraries
import os
import sys
import subprocess
import importlib
import traceback
import socket
import shutil
import ssl
import asyncio

# Magic helper
def installinate(module_name, package_name=None):
  if package_name is None:
    package_name = module_name # common for 90% of python s/w
  try:
    return importlib.import_module(module_name)
  except:
    traceback.print_exc()
    subprocess.run([
      sys.executable, *( '-m pip install --user'.split() ), package_name
    ])
  
  return importlib.import_module(module_name)

# Begin 3rd-party libraries
aiohttp = installinate('aiohttp')
import aiohttp.web

# Helper function to import single function from a file path
def fn_from(file_path, func_name):
  file_dir = os.path.dirname(file_path)
  module_name = os.path.basename(file_path).replace('.py', '').replace('.Py', '').replace('.pY', '').replace('.PY', '')
  try:
    if not file_dir in sys.path:
      sys.path.append(file_dir)
    return getattr(
      importlib.import_module(module_name),
      func_name
    )
  except:
    traceback.print_exc()
    return None

# SSL utility
def get_ssl_cert_and_key_or_generate(ssl_dir='ssl'):
  #ssl_dir = 'ssl'
  if not os.path.exists(ssl_dir):
    os.makedirs(ssl_dir)
  
  key_file = os.path.join(ssl_dir, 'server.key')
  cert_file = os.path.join(ssl_dir, 'server.crt')

  if os.path.exists(key_file) and os.path.exists(cert_file):
    return cert_file, key_file
  else:
    if os.path.exists(key_file):
      os.remove(key_file)
    if os.path.exists(cert_file):
      os.remove(cert_file)
  
  if not shutil.which('openssl'):
    raise Exception('Cannot find the tool "openssl", please install this so we can generate ssl certificates for our servers! Alternatively, manually create the files {} and {}.'.format(cert_file, key_file))

  generate_cmd = ['openssl', 'req', '-x509', '-sha256', '-nodes', '-days', '28', '-newkey', 'rsa:2048', '-keyout', key_file, '-out', cert_file]
  subprocess.run(generate_cmd, check=True)

  return cert_file, key_file


def get_local_ip():
  """Try to determine the local IP address of the machine."""
  try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

      # Use Google Public DNS server to determine own IP
      sock.connect(('8.8.8.8', 80))

      return sock.getsockname()[0]

  except socket.error:
      try:
          return socket.gethostbyname(socket.gethostname())
      except socket.gaierror:
          return '127.0.0.1'
  finally:
      sock.close() 


async def start_background_tasks(server):
  loop = asyncio.get_event_loop()
  task = loop.create_task(heartbeat_task())

async def heartbeat_task():
  while True:
    try:
      print('Heartbeat!')
    except:
      traceback.print_exc()
    
    await asyncio.sleep(5.0)



def main(args=sys.argv):
  
  cert_file, key_file = get_ssl_cert_and_key_or_generate(
    os.environ.get('PEC_POC_SSL_DIR', 'ssl')
  )
  
  w = os.environ.get('PEC_POC_WWW_DIR', None)
  if w is None:
    w = os.path.abspath('www')
  
  if not os.path.exists(w):
    raise Exception(f'Cannot find the www directory at {w}, please execute server.py in the repo root or specify PEC_POC_WWW_DIR=/path/to/wherever')

  server = aiohttp.web.Application()

  server.add_routes([
    aiohttp.web.get('/', lambda req: aiohttp.web.FileResponse(f'{w}/index.html') ),
    aiohttp.web.get('/ws', fn_from(f'{w}/ws.py', 'handle_ws')),
    # Useful on ios to install our temporary ssl cert system-wide
    #aiohttp.web.get('/server.crt', lambda req: aiohttp.web.FileResponse(cert_file) ),
  ])

  server.on_startup.append(start_background_tasks)

  ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
  ssl_ctx.load_cert_chain(cert_file, key_file)

  port_num = int(os.environ.get('PEC_POC_HTTP_PORT', '4431'))

  print(f'Hosting on: https://{get_local_ip()}:{port_num}/')

  aiohttp.web.run_app(server, ssl_context=ssl_ctx, port=port_num)



if __name__ == '__main__':
  main()