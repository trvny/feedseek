import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const script = await readFile(new URL("../webmcp.js", import.meta.url), "utf8");
const catalog = {
  format: "feedseek-model-feed-catalog", version: 1,
  feeds: [{key:"jbzd",title:"JBZD",feed_url:"https://rss.bartek.lol/jbzd.xml",model_feed_url:"https://rss.bartek.lol/jbzd.json"}],
};
const model = {
  format: "feedseek-model-feed", version: 1,
  items: [
    {id:"one",title:"Cat GIF",text:"Funny cat",tags:["cats"],url:"https://example.com/1",image:"https://example.com/1.gif"},
    {id:"two",title:"Dog meme",text:"Woof",tags:["dogs"],url:"https://example.com/2"},
  ],
};
function createTools() {
  const tools = new Map();
  const requested = [];
  const document = {
    baseURI:"https://rss.bartek.lol/",
    modelContext:{registerTool(tool) { tools.set(tool.name,tool); return Promise.resolve(); }},
    querySelector(selector) {return selector==="#search"?{}:null;},
    querySelectorAll(selector) {return selector===".card"?[{}]:[];},
  };
  const fetch = async (url) => {
    const href = String(url);
    requested.push(href);
    if (href==="https://rss.bartek.lol/model-feeds.json") return Response.json(catalog);
    if (href==="https://rss.bartek.lol/jbzd.json") return Response.json(model);
    throw Error("Unexpected fetch: "+href);
  };
  vm.runInNewContext(script, {
    document,window:{addEventListener(){}},fetch,console,URL,
    AbortController,AbortSignal,Symbol,Promise,
  });
  return {tools,requested};
}
test("WebMCP previews verified Model Feeds with bounded search and pagination", async () => {
  const {tools,requested}=createTools();
  const call=tools.get("preview_feed_entries");
  assert.ok(call);
  assert.equal(call.annotations.readOnlyHint,true);
  const result=await call.execute({source_key:"jbzd",query:"cat",limit:1});
  assert.equal(result.total,1);
  assert.equal(result.entries[0].id,"one");
  assert.equal(result.entries[0].image,"https://example.com/1.gif");
  assert.equal(result.next_offset,null);
  assert.deepEqual(requested,[
    "https://rss.bartek.lol/model-feeds.json","https://rss.bartek.lol/jbzd.json",
  ]);
  const page=await call.execute({source_key:"jbzd",limit:1,offset:1});
  assert.equal(page.total,2);
  assert.equal(page.entries[0].id,"two");
  assert.equal(page.entries[0].image,null);
});
test("WebMCP never fetches arbitrary model URLs", async () => {
  const {tools,requested}=createTools();
  const call=tools.get("preview_feed_entries");
  await assert.rejects(call.execute({source_key:"../../private"}),/Invalid/);
  await assert.rejects(call.execute({source_key:"unknown"}),/Unknown/);
  await assert.rejects(call.execute({source_key:"jbzd",limit:999}),/limit/);
  assert.deepEqual(requested,["https://rss.bartek.lol/model-feeds.json"]);
});
