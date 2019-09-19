import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
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
