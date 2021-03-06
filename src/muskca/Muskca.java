/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

package muskca;

import Alignment.Aligner;
import Alignment.AlignerLogMap;
import Candidate.NodeCandidate.ClassCandidate;
import Candidate.NodeCandidate.IndividualCandidate;
import Candidate.NodeCandidate.NodeCandidate;
import MultiSources.Extension;
import MultiSources.Fusionner;
import MultiSources.Solver.ExtensionSolver;
import Source.Source;
import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import org.apache.commons.io.FileUtils;

/**
 *
 * @author murloc
 */
public class Muskca 
{
    public static String muskcaVersion = "Alpha1";
    public static String dateBegin = "";
    public static String dateEnd = "";
    
    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) 
    {   
        
        /*
         * TODO : 
            -> Change trust score comutation (trust mix)
            -> Implements the Log4J lib to improve the logs
            -> Clean up the Fusionner class and the Source class
         */
        
        cleanTempDirectory();
        Muskca.dateBegin = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
        
        ParamsReader params = new ParamsReader();
        
        String projectName = params.getParam("projectName");
        String moduleFile = params.getParam("moduleFile");
        ArrayList<Source> sources = params.getSources();
        ArrayList<String> urisRelImp = params.getArrayParams("relImps");
        ArrayList<String> urisLabelsImp = params.getArrayParams("labelRelImps");
         
        HashMap<String, String> mongoDbs = params.getSubParams("mongoDbs");

        HashMap<String, String> outputParams = params.getSubParams("output");
        String provoFile = outputParams.get("provoFile");
        String spOutProvo = outputParams.get("spOutProvo");
        String baseUriMuskca = outputParams.get("baseUri")+projectName+"/";

        HashMap<String, String> fusionnerParams = params.getSubParams("fusionner");
        Fusionner fusionner = new Fusionner(mongoDbs.get("mongodb"));
        
        String dataProlog = fusionner.initPrologSources(sources);
        
        StringBuilder dataIndProlog = new StringBuilder(dataProlog);
        StringBuilder dataClassProlog = new StringBuilder(dataProlog);
        for(int i = 0; i< sources.size(); i++)
        {
            Source s1 = sources.get(i);
            System.out.println("Start analyze source : "+s1.getName()+" ("+(i+1)+"/"+sources.size()+")");
            for(int j = i+1; j< sources.size(); j++)
            {
                Source s2 = sources.get(j);
                
                System.out.println(s1.getName()+"/"+s2.getName()+ ": ");
                Aligner aligner = new AlignerLogMap(fusionner, s1, s2);
                System.out.println("Aligner ended !");
                aligner.alignSources(0); // score min = 0 to keep all alignment (filter will be done by taken the first one)
                dataIndProlog = dataIndProlog.append(aligner.getPrologIndAligns());
                dataClassProlog = dataClassProlog.append(aligner.getPrologClassAligns());
            }
        }
        for(Source s : sources)
        {
            dataClassProlog = dataClassProlog.append(s.classesToPrologData());
            dataIndProlog = dataIndProlog.append(s.indsToPrologData());
        }
        
         System.out.println("BEGIN COMPUTE Classes CANDIDATE");
        ArrayList<ClassCandidate> candidatesClass = fusionner.computeClassCandidate(mongoDbs.get("classCandidateMongoCol"), dataClassProlog);
        
        System.out.println("BEGIN COMPUTE Ind. CANDIDATE");
        ArrayList<IndividualCandidate> candidatesInd = fusionner.computeIndCandidate(mongoDbs.get("indivCandidateMongoCol"), dataIndProlog, sources.size());
        
        int nbCandidates = candidatesClass.size()+candidatesInd.size();
        StringBuilder dataForExtensions = fusionner.allCandidatesToPrologData();
        
        System.out.println("Begin compute extensions (nb candidates : "+nbCandidates+")");
        ArrayList<Extension> extensions =fusionner.computeExtensions(dataForExtensions, nbCandidates);
        
        String extExport = "";
        String extPl = "";
        for(Extension ext : extensions)
        {
            extExport += ext.toString();
            extPl += ext.toPrologData();
        }
        
        Muskca.dateEnd = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
        Muskca.exportFile(extExport, projectName+"_Extensions_data.txt");
        Muskca.exportFile(extPl, projectName+"_Extensions_data.ecl");
        System.out.println("End treatment ("+extensions.size()+" extensions generated)");
        System.out.println(Muskca.dateBegin+" ----> "+Muskca.dateEnd);
        System.exit(0);
        
        String retRelCandidate = "";
        for(String uriRel : urisRelImp)
        {
            fusionner.computeRelationCandidate(mongoDbs.get("objPropArcCandidateMongoCol"), uriRel);
        }
        fusionner.computeTypeCandidate(mongoDbs.get("typeArcCandidateMongoCol"));
        fusionner.computeLabelCandidate(mongoDbs.get("labelArcCandidateMongoCol"), urisLabelsImp);
        
        
        System.out.println("NB SAVED ON MONGO : "+fusionner.nbMongoSaved);
        
        Muskca.dateEnd = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
        
        
        String retClassFile = fusionner.allClassCandidatesToString();
        System.out.println("EXPORTING class stats file ...");
         Muskca.exportFile(retClassFile, projectName+"_HypClassCandidate_stats.txt");
        //AlignRKBAgroTaxon.exportFile(fusionner.allCandidatesToCSV(), projectName+".csv");
        System.out.println("FILE CLASS PERSO EXPORTED");
        
        String retFile = retClassFile+"\n\n"+fusionner.allCandidatesToString();
        System.out.println("EXPORTING stats file ...");
         Muskca.exportFile(retFile, projectName+"_HypCandidate_stats.txt");
        //AlignRKBAgroTaxon.exportFile(fusionner.allCandidatesToCSV(), projectName+".csv");
        System.out.println("FILE PERSO EXPORTED");
        
       /* System.out.println("EXPORTING provo owl file ...");
        SparqlProxy spProvo = fusionner.allCandidatesToProvo(provoFile, spOutProvo, adomFile, baseUriMuskca);
        //Muskca.exportFile(spProvo., projectName+"_CandProvo.owl");
        spProvo.writeKBFile(projectName+"_CandProvo");
        System.out.println("FILE PROVO EXPORTED");*/
        
     }
    
    
    private static void cleanTempDirectory()
    {
        try 
        { 
            FileUtils.cleanDirectory(new File("out/temp/"));
        } 
        catch (IOException ex) 
        {
            System.err.println("Error during cleaning the out/temp/ directory");
        }
    }
    
    private static void exportFile(String content, String projectName)
    {
        cleanTempDirectory();
        String dateFileName = new SimpleDateFormat("dd-MM_HH-mm_").format(new Date());
        try {
            FileUtils.write(new File("out/"+dateFileName+"_Fusion_"+projectName), content);
        } catch (IOException ex) {
            //System.out.println(triplesFusionStats);
            System.out.println("ERROR DURING OUTPUT FILE");
        }
    }
}
