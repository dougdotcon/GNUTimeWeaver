/* SPDX-License-Identifier: AGPL-3.0-or-later */
#include "llama.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <process.h>
#include <string>
#include <vector>
#include <algorithm>

static int fail(const char *m) { std::fprintf(stderr, "%s\n", m); return 2; }
static bool write_all(const std::string &p, const void *d, size_t n) {
    std::ofstream f(p, std::ios::binary | std::ios::trunc);
    f.write(static_cast<const char *>(d), static_cast<std::streamsize>(n));
    f.flush(); return f.good();
}
static std::vector<uint8_t> read_all(const std::string &p) {
    std::ifstream f(p, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
}
static bool write_tokens(const std::string &p, const std::vector<llama_token> &v) {
    return write_all(p, v.data(), v.size()*sizeof(llama_token));
}
static std::vector<llama_token> read_tokens(const std::string &p) {
    auto b=read_all(p); std::vector<llama_token> v(b.size()/sizeof(llama_token));
    if(!b.empty()) std::memcpy(v.data(),b.data(),v.size()*sizeof(llama_token)); return v;
}
static uint64_t token_checksum(const std::vector<llama_token> &v) {
    uint64_t h=1469598103934665603ULL;
    for(auto t:v){ h^=(uint32_t)t; h*=1099511628211ULL; }
    return h;
}
static std::vector<llama_token> continue_greedy(llama_context *ctx, const llama_vocab *vocab,
                                                llama_token first, int count) {
    llama_sampler *s=llama_sampler_init_greedy(); std::vector<llama_token> out;
    llama_token cur=first;
    for(int i=0;i<count;i++) {
        out.push_back(cur);
        if(llama_vocab_is_eog(vocab,cur) || llama_decode(ctx,llama_batch_get_one(&cur,1))!=0) break;
        cur=llama_sampler_sample(s,ctx,-1);
    }
    llama_sampler_free(s); return out;
}
int main(int argc, char **argv) {
    if (argc < 4) return fail("usage: runner checkpoint|restore MODEL WORKSPACE [prefix_tokens]");
    const std::string mode=argv[1], model_path=argv[2], ws=argv[3];
#ifdef TIMEWEAVER_PROFILE_ACCEPTANCE
    if (model_path.find("qwen2.5-coder-0.5b-q8_0.gguf") == std::string::npos)
        return fail("MODEL_NOT_AUTHORIZED_FOR_ACCEPTANCE");
#endif
    ggml_backend_load_all();
    llama_model_params mp=llama_model_default_params(); mp.n_gpu_layers=0;
    llama_model *model=llama_model_load_from_file(model_path.c_str(),mp);
    if(!model) return fail("MODEL_LOAD_FAILED");
    llama_context_params cp=llama_context_default_params();
    cp.n_ctx=4096; cp.n_batch=2048; cp.n_ubatch=512; cp.n_seq_max=1;
    llama_context *ctx=llama_init_from_model(model,cp);
    if(!ctx) return fail("CONTEXT_CREATE_FAILED");
    const llama_vocab *vocab=llama_model_get_vocab(model);
    const std::string state_path=ws+"/sequence.bin", tokens_path=ws+"/tokens.bin";
    const std::string expected_path=ws+"/expected.bin", pending_path=ws+"/pending.bin", token_hash_path=ws+"/tokens.hash";
    int result=0;
    if(mode=="checkpoint") {
        std::string prompt;
        while(prompt.size()<12000) prompt += "Once upon a time, Lily explored the garden and learned a new lesson. ";
        const size_t requested = argc >= 5 ? std::stoul(argv[4]) :
#ifdef TIMEWEAVER_PROFILE_ACCEPTANCE
            512;
#else
            128;
#endif
        int nt=-llama_tokenize(vocab,prompt.c_str(),prompt.size(),nullptr,0,true,true);
        std::vector<llama_token> toks(nt);
        if(llama_tokenize(vocab,prompt.c_str(),prompt.size(),toks.data(),toks.size(),true,true)<0) result=fail("TOKENIZE_FAILED");
        else if(toks.size() < requested) result=fail("PREFIX_FIXTURE_TOO_SHORT");
        else { toks.resize(requested);
        if(llama_decode(ctx,llama_batch_get_one(toks.data(),toks.size()))!=0) result=fail("PREFILL_FAILED");
        else {
            size_t n=llama_state_seq_get_size(ctx,0); std::vector<uint8_t> state(n);
            size_t got=llama_state_seq_get_data(ctx,state.data(),state.size(),0);
            llama_sampler *s=llama_sampler_init_greedy();
            llama_token pending=llama_sampler_sample(s,ctx,-1); llama_sampler_free(s);
            const uint64_t token_hash=token_checksum(toks);
            if(got!=n || !write_all(state_path,state.data(),state.size()) ||
               !write_tokens(tokens_path,toks) || !write_all(pending_path,&pending,sizeof pending) ||
               !write_all(token_hash_path,&token_hash,sizeof token_hash)) result=fail("STATE_WRITE_FAILED");
            else {
                auto expected=continue_greedy(ctx,vocab,pending,16);
                if(!write_tokens(expected_path,expected)) result=fail("EXPECTED_WRITE_FAILED");
                else std::printf("{\"mode\":\"checkpoint\",\"process_id\":%d,\"expected_prefix_tokens\":%zu,\"prefix_tokenizer_invocations\":2,\"prefix_tokens_decoded\":%zu,\"generated_tokens\":%zu,\"state_bytes\":%zu,\"state_bytes_written\":%zu}\n",_getpid(),toks.size(),toks.size(),expected.size(),n,got);
            }
        }}
    } else if(mode=="restore") {
        auto state=read_all(state_path); auto toks=read_tokens(tokens_path);
        auto pend=read_all(pending_path); auto expected=read_tokens(expected_path);
        auto th=read_all(token_hash_path); uint64_t expected_hash=0;
        if(th.size()==sizeof expected_hash) std::memcpy(&expected_hash,th.data(),sizeof expected_hash);
        if(pend.size()!=sizeof(llama_token)) return fail("PENDING_TOKEN_INVALID");
        llama_token pending; std::memcpy(&pending,pend.data(),sizeof pending);
        size_t nt=toks.size();
        size_t got=llama_state_seq_set_data(ctx,state.data(),state.size(),0);
        llama_pos pmin=llama_memory_seq_pos_min(llama_get_memory(ctx),0);
        llama_pos pmax=llama_memory_seq_pos_max(llama_get_memory(ctx),0);
        auto actual=continue_greedy(ctx,vocab,pending,16);
        bool equal=actual==expected;
        std::printf("{\"mode\":\"restore\",\"process_id\":%d,\"restored_prefix_tokens\":%zu,\"prefix_tokenizer_invocations_after_restore\":0,\"prefix_tokens_decoded_after_restore\":0,\"generated_tokens_after_restore\":%zu,\"greedy_token_ids_equal\":%s,\"state_bytes_read\":%zu,\"state_bytes_restored\":%zu,\"restored_min_position\":%d,\"restored_max_position\":%d}\n",_getpid(),nt,actual.size(),equal?"true":"false",state.size(),got,(int)pmin,(int)pmax);
        result=(got==state.size() && pmax+1==(llama_pos)nt && token_checksum(toks)==expected_hash && equal)?0:fail("RESTORE_VALIDATION_FAILED");
    } else if(mode=="branch") {
        if(argc<5) return fail("branch requires suffix");
        auto state=read_all(state_path); auto toks=read_tokens(tokens_path);
        if(llama_state_seq_set_data(ctx,state.data(),state.size(),0)!=state.size()) return fail("BRANCH_RESTORE_FAILED");
        std::string suffix=argv[4];
        int ns=-llama_tokenize(vocab,suffix.c_str(),suffix.size(),nullptr,0,false,true);
        std::vector<llama_token> st(ns);
        if(llama_tokenize(vocab,suffix.c_str(),suffix.size(),st.data(),st.size(),false,true)<0 ||
           llama_decode(ctx,llama_batch_get_one(st.data(),st.size()))!=0) return fail("BRANCH_SUFFIX_FAILED");
        llama_sampler *s=llama_sampler_init_greedy(); llama_token first=llama_sampler_sample(s,ctx,-1); llama_sampler_free(s);
        auto out=continue_greedy(ctx,vocab,first,8);
        uint64_t h=1469598103934665603ULL;
        for(auto t:out){ h^=(uint32_t)t; h*=1099511628211ULL; }
        std::printf("{\"mode\":\"branch\",\"restored_prefix_tokens\":%zu,\"prefix_tokenizer_invocations_after_restore\":0,\"prefix_tokens_decoded_after_restore\":0,\"suffix_tokens_tokenized_after_restore\":%zu,\"suffix_tokens_decoded_after_restore\":%zu,\"generated_tokens_after_restore\":%zu,\"first_generated_token\":%d,\"continuation_hash\":\"%016llx\"}\n",toks.size(),st.size(),st.size(),out.size(),out.empty()?-1:out[0],(unsigned long long)h);
    } else result=fail("UNKNOWN_MODE");
    llama_free(ctx); llama_model_free(model); return result;
}
