
import aiohttp.web

async def handle_ws(req):
  peername = req.transport.get_extra_info('peername')
  host = 'unk'
  if peername is not None:
    host, port = peername

  print('ws req from {}'.format(host))

  ws = aiohttp.web.WebSocketResponse()
  await ws.prepare(req)

  return ws

