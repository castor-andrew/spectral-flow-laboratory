import asyncio, json, struct
import websockets
async def main():
 async with websockets.connect("ws://127.0.0.1:8765/ws") as ws:
  b=await ws.recv(); h,p=struct.unpack_from("<II",b); pad=(-(8+h))%4; start=8+h+pad
  meta=json.loads(b[8:8+h]); print({"packet":len(b),"header":h,"pad":pad,"start":start,"pbytes":p,"remainder":len(b)-start-p,"remainder_mod4":(len(b)-start-p)%4,"meta":meta["layout"]})
asyncio.run(main())
