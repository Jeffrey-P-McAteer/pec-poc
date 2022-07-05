
# Builting
import traceback

# 3rdparty
import aiohttp.web

async def maybe_await(fun, on_exception=None):
  try:
    return await fun()
  except:
    traceback.print_exc()
    if on_exception != None:
      return on_exception()
    return None

all_ws = []

async def handle_ws(req):
  global all_ws
  peername = req.transport.get_extra_info('peername')
  host = 'unk'
  if peername is not None:
    host, port = peername

  print('ws req from {}'.format(host))

  ws = aiohttp.web.WebSocketResponse()
  await ws.prepare(req)

  all_ws.append(ws)

  async for msg in ws:
    try:
      if msg.type == aiohttp.WSMsgType.TEXT:
        print('WS From {}: {}'.format(host, msg.data))
        
        if msg.data.startswith('message='):
          continue

        # Broadcast to everyone else
        # with CodeTimer('Broadcast to everyone else', unit='ms'):
        #   await asyncio.gather(*[ maybe_await(lambda: w.send_str(msg.data)) for w in all_ws if w != ws])
        await asyncio.gather(*[ maybe_await(lambda: w.send_str(msg.data)) for w in all_ws if w != ws])
        
      elif msg.type == aiohttp.WSMsgType.ERROR:
        print('ws connection closed with exception {}'.format(ws.exception()))
    except:
      traceback.print_exc()

  all_ws.remove(ws)

  return ws

