/*
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org>
*/

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
// add mvn dependency: com.googlecode.json-simple:json-simple
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
// add mvn dependency: org.apache.httpcomponents:httpclient
import org.apache.http.HttpResponse;
import org.apache.http.util.EntityUtils;
import org.apache.http.client.HttpClient;
import org.apache.http.entity.StringEntity;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.impl.client.HttpClientBuilder;

public class JavaClient {
    public static void main (String [] args) throws IOException {
        // read the model
        String content = new String ( Files.readAllBytes( Paths.get("../src/test/gene-filter-example-2.xml") ) );
        
        // create a job, here using json-simple
        JSONObject export = new JSONObject();
        export.put ("network_type", "en");
        export.put ("network_format", "dot");
        
        JSONObject filter = new JSONObject();
        JSONArray tmp = new JSONArray ();
        tmp.add ("a");
        tmp.add ("d");
        filter.put ("species", tmp);
        
        tmp = new JSONArray ();
        tmp.add ("r2");
        filter.put ("reactions", tmp);
        
        tmp = new JSONArray ();
        tmp.add ("gene_abc");
        tmp.add ("gene_x");
        filter.put ("enzymes", tmp);
        
        tmp = new JSONArray ();
        tmp.add ("b + c");
        tmp.add ("x + Y");
        tmp.add ("b_098 + r_abc");
        filter.put ("enzyme_complexes", tmp);
        
        JSONObject job = new JSONObject();
        job.put ("export", export);
        job.put ("filter", filter);
        job.put ("file", content);

        // send an HTTP POST request
        HttpPost request = new HttpPost("https://gemtractor.bio.informatik.uni-rostock.de/api/execute");
        request.addHeader("content-type", "application/json");
        request.setEntity(new StringEntity(job.toString()));

        HttpClient httpClient = HttpClientBuilder.create().build();
        HttpResponse response = httpClient.execute(request);
        
        // print the results
        System.out.println (EntityUtils.toString(response.getEntity(), "UTF-8"));
    }
}
