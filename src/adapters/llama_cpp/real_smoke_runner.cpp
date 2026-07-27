/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "llama.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

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
int main(int argc, char **argv) {
    if (argc < 4) return fail("usage: tw-real-smoke checkpoint|restore MODEL WORKSPACE");
    const std::string mode=argv[1], model_path=argv[2], ws=argv[3];
    ggml_backend_load_all();
    llama_model_params mp=llama_model_default_params(); mp.n_gpu_layers=0;
    llama_model *model=llama_model_load_from_file(model_path.c_str(),mp);
    if(!model) return fail("MODEL_LOAD_FAILED");
    llama_context_params cp=llama_context_default_params();
    cp.n_ctx=128; cp.n_batch=128; cp.n_ubatch=128; cp.n_seq_max=1;
    llama_context *ctx=llama_init_from_model(model,cp);
    if(!ctx) return fail("CONTEXT_CREATE_FAILED");
    const llama_vocab *vocab=llama_model_get_vocab(model);
    const std::string state_path=ws+"/sequence.bin", tokens_path=ws+"/tokens.bin";
    int result=0;
    if(mode=="checkpoint") {
        std::string prompt;
        while(prompt.size()<420) prompt += "Once upon a time, Lily explored the garden and learned a new lesson. ";
        int nt=-llama_tokenize(vocab,prompt.c_str(),prompt.size(),nullptr,0,true,true);
        std::vector<llama_token> toks(nt);
        if(llama_tokenize(vocab,prompt.c_str(),prompt.size(),toks.data(),toks.size(),true,true)<0) result=fail("TOKENIZE_FAILED");
        else if(llama_decode(ctx,llama_batch_get_one(toks.data(),toks.size()))!=0) result=fail("PREFILL_FAILED");
        else {
            size_t n=llama_state_seq_get_size(ctx,0); std::vector<uint8_t> state(n);
            size_t got=llama_state_seq_get_data(ctx,state.data(),state.size(),0);
            if(got!=n || !write_all(state_path,state.data(),state.size()) ||
               !write_all(tokens_path,toks.data(),toks.size()*sizeof(llama_token))) result=fail("STATE_WRITE_FAILED");
            else std::printf("{\"mode\":\"checkpoint\",\"expected_prefix_tokens\":%zu,\"prefix_tokenizer_invocations\":2,\"prefix_tokens_decoded\":%zu,\"state_bytes\":%zu,\"state_bytes_written\":%zu}\n",toks.size(),toks.size(),n,got);
        }
    } else if(mode=="restore") {
        auto state=read_all(state_path); auto raw=read_all(tokens_path);
        size_t nt=raw.size()/sizeof(llama_token);
        size_t got=llama_state_seq_set_data(ctx,state.data(),state.size(),0);
        llama_pos pmin=llama_memory_seq_pos_min(llama_get_memory(ctx),0);
        llama_pos pmax=llama_memory_seq_pos_max(llama_get_memory(ctx),0);
        std::printf("{\"mode\":\"restore\",\"restored_prefix_tokens\":%zu,\"prefix_tokenizer_invocations_after_restore\":0,\"prefix_tokens_decoded_after_restore\":0,\"state_bytes_read\":%zu,\"state_bytes_restored\":%zu,\"restored_min_position\":%d,\"restored_max_position\":%d}\n",nt,state.size(),got,(int)pmin,(int)pmax);
        result=(got==state.size() && pmax+1==(llama_pos)nt)?0:fail("RESTORE_VALIDATION_FAILED");
    } else result=fail("UNKNOWN_MODE");
    llama_free(ctx); llama_model_free(model); return result;
}
